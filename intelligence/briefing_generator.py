import logging
import time
from typing import Optional

from config import env_ini as env# noqa: F401
from utils.prompt_loader import load_prompt
from google import genai
from google.genai.errors import APIError

from urllib.parse import urlparse
from google.genai import types
import re
from utils.text_utils import build_link_label


logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]

MAX_ATTEMPTS = 3
REF_PATTERN = re.compile(r"\[(A\d+)\]")
 
 
class BriefingGenerationError(RuntimeError):
    """Raised when synthesis fails on every model, so the scheduled run fails loudly."""

def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return a secret from Streamlit or environment variables."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError

        if hasattr(st, "secrets"):
            try:
                return st.secrets.get(name, env.get_env_var(name))
            except StreamlitSecretNotFoundError:
                return env.get_env_var(name)
    except ModuleNotFoundError:
        pass

    return env.get_env_var(name)


# Set up global client initialization for this module
key = get_secret("GOOGLE_API_KEY")
if not key:
    raise ValueError(
        "GOOGLE_API_KEY is not set in the environment variables or Streamlit secrets."
    )

client = genai.Client(api_key=key)


def create_intelligence_briefing(
        articles: list[dict], 
        events: list[dict],
        briefings: list[str] | None = None)-> str:
    """Assemble the prompt, synthesize the briefing, and resolve its citations."""

    prompt, id_to_url = build_prompt(
        load_prompt("daily_briefing.txt"),
        articles,
        events,
        briefings,
    )
    return generate_briefing(client, prompt, id_to_url),prompt

def build_prompt(
    prompt: str,
    articles: list[dict],
    events: list[dict],
    recent_briefings: list[str] | None = None,
) -> tuple[str, dict[str, str]]:
    """
    Builds the briefing prompt from structured data.
 
    Articles get stable [A#] reference ids. The model cites only those ids —
    never URLs — so it cannot invent a link; real links are substituted after
    generation. Events reference the same ids, giving both blocks one id space.
 
    Events with material_change=False are routed to a separate "unchanged" list
    here, in code, rather than asking the prompt to re-decide suppression.
 
    Returns:
        (prompt_text, id_to_url) — the map is required by generate_briefing().
    """

    recent_briefings = recent_briefings or []

    # Articles: assign ids, build both lookups in one pass.
    id_to_url, url_to_id, article_lines = {}, {}, []
    for i, art in enumerate(articles, start=1):
        ref, url = f"A{i}", art.get("link") or ""
        id_to_url[ref] = url
        if url:
            url_to_id[url] = ref
        summary = art.get("ai_summary") or art.get("raw_summary") or ""
        article_lines.append(
            f"[{ref}] {art.get('title', 'Untitled')} "
            f"({art.get('category', 'unknown')}, score {art.get('score', '—')})\n"
            f"      {summary}"
        )
 
    # Events: classify NEW vs DEVELOPING, gate out unchanged ones.
    featured, unchanged = [], []
    for ev in events:
        name = ev.get("name") or ev.get("title") or "Untitled event"
        is_new = ev.get("first_seen_at") == ev.get("last_updated_at")
 
        # material_change is False only when explicitly set; unknown (None)
        # still features, so a partial schema never silently hides a story.
        if not is_new and ev.get("material_change") is False:
            unchanged.append(f"- {name}")
            continue
 
        refs = " ".join(
            f"[{url_to_id[link['url']]}]"
            for link in (ev.get("article_links") or [])
            if link.get("url") in url_to_id
        ) or "(none in today's set)"
 
        block = [
            f"EVENT: {name}   [{'NEW' if is_new else 'DEVELOPING'}]",
            f"  Sources: {ev.get('source_count', 'unknown')} | Category: {ev.get('category', 'unknown')}",
            f"  Summary: {ev.get('summary') or '(none)'}",
        ]
        if not is_new and ev.get("delta_text"):
            block.append(f"  What's new today: {ev['delta_text']}")
        block.append(f"  Today's articles: {refs}")
        featured.append("\n".join(block))
 
    prompt_text = f"""{prompt}
 
------------------------------------
TODAY'S ARTICLES
 
{chr(10).join(article_lines) or "(none)"}
 
------------------------------------
TODAY'S EVENTS
 
{(chr(10) + chr(10)).join(featured) or "(none)"}
 
------------------------------------
UNCHANGED EVENTS (one-line "Still Developing" mentions only)
 
{chr(10).join(unchanged) or "(none)"}
 
------------------------------------
RECENT BRIEFINGS (avoid repeating these — do not copy their wording)
 
{(chr(10) + chr(10)).join(b[:6000] for b in recent_briefings[:2]) or "(none)"}
"""
    return prompt_text, id_to_url

def resolve_citations(briefing: str, id_to_url: dict[str, str]) -> str:
    """
    Replace each [A#] reference with a real markdown link, deduplicated by
    source per line. Ids absent from the map were invented by the model, so
    they are stripped and logged rather than rendered as dead links.
    """
    unknown = []
 
    def render_line(line: str) -> str:
        seen: set[str] = set()
 
        def replace(match: re.Match) -> str:
            ref = match.group(1)
            url = id_to_url.get(ref)
            if not url:
                unknown.append(ref)
                return ""
            domain = (urlparse(url).netloc or "").lower().replace("www.", "")
            if domain in seen:
                return ""
            seen.add(domain)
            return f"[{build_link_label(url)}]({url})"
 
        return REF_PATTERN.sub(replace, line)
 
    resolved = "\n".join(render_line(line) for line in briefing.splitlines())
    if unknown:
        logger.warning("Model cited unknown reference ids %s; removed.", sorted(set(unknown)))
    return resolved

def generate_briefing(client, prompt: str, id_to_url: dict[str, str],
                      temperature: float = 0.35) -> str:
    """
    Generates the briefing, retrying each model with backoff before falling back.
 
    Raises BriefingGenerationError when every model is exhausted. Do not catch
    it upstream: a failed run must exit non-zero so the scheduled workflow
    reports failure instead of publishing an error message as a briefing.
    """
    for model_name in FALLBACK_MODELS:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=temperature),
                )
                text = getattr(response, "text", None)
                if not text or not text.strip():
                    # Empty output means a safety block or token limit — a
                    # failure, not a briefing. Retrying the same model won't help.
                    logger.warning("Model %s returned no text; falling back.", model_name)
                    break
 
                logger.info("Briefing generated with model %s.", model_name)
                return resolve_citations(text, id_to_url)
 
            except APIError as api_err:
                code = getattr(api_err, "code", None)
                if code not in (429, 503):
                    # 400/403/404 are deterministic; retrying is pointless.
                    logger.error("Non-retryable API error on %s (%s): %s",
                                 model_name, code, api_err.message)
                    break
                # 429 is project-wide quota, so backing off beats switching models.
                wait = (60 if code == 429 else 5) * attempt
                logger.warning("Model %s returned %s. Retry %d/%d in %ds.",
                               model_name, code, attempt, MAX_ATTEMPTS, wait)
                time.sleep(wait)
 
            except Exception:
                logger.exception("Unexpected failure on %s (attempt %d).", model_name, attempt)
                time.sleep(5 * attempt)
 
    raise BriefingGenerationError(
        "Briefing synthesis failed: all fallback models exhausted."
    )
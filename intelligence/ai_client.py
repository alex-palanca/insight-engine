import asyncio
import logging

from google import genai
from google.genai import types
from google.genai.errors import APIError

import config.env_ini as env
from config.score_system import BatchEvaluation
from utils import prompt_loader

logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

_client: genai.Client | None = None

def get_client() -> genai.Client:
    global _client

    if _client is None:
        key = env.get_env_var("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "GOOGLE_API_KEY is not set in the environment variables "
                "or Streamlit secrets."
            )
        _client = genai.Client(api_key=key)

    return _client

FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash"
]


async def async_evaluate_batch(batch_text: str) -> tuple[BatchEvaluation | None, str | None, dict]:
    """
    Sends a batch of articles to Gemini.

    Returns:
        A tuple of (evaluation result, model actually used).
        Both values are None if every fallback model failed.
    """
    client = get_client()
    
    for model_name in FALLBACK_MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=batch_text,
                config=types.GenerateContentConfig(
                    system_instruction=prompt_loader.load_prompt("article_scoring.txt"),
                    response_mime_type="application/json",
                    response_schema=BatchEvaluation,
                    temperature=0.1
                ),
            )

            usage = getattr(response, "usage_metadata", None)
            token_usage = {
                "prompt_tokens": getattr(usage, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(usage, "candidates_token_count", 0) or 0,
                "total_tokens": getattr(usage, "total_token_count", 0) or 0,
            }

            return BatchEvaluation.model_validate_json(response.text), model_name, token_usage

        except APIError as api_err:
            if api_err.code == 503:
                logger.warning("Model %s is overloaded (503). Trying fallback model.", model_name)
                await asyncio.sleep(0.5)
                continue

            if api_err.code == 429:
                logger.warning("Rate limit exceeded for model %s (429). Trying fallback model.", model_name)
                await asyncio.sleep(0.5)
                continue

            logger.error(
                "Critical Google API error on model %s (%s): %s",
                model_name,
                api_err.code,
                api_err.message,
            )
            break

        except Exception:
            logger.exception("Unexpected evaluation failure on model %s.", model_name)
            break

    logger.error("All fallback models were exhausted. Batch evaluation skipped.")
    
    return None,None, None

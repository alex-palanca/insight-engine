import os
from dotenv import load_dotenv 
from google import genai
from datetime import datetime
from storage.storage_service import upload_daily_briefing
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Define Local or Remote 
local = 0


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return a secret from Streamlit or environment variables."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError

        if hasattr(st, "secrets"):
            try:
                return st.secrets.get(name, os.getenv(name, default))
            except StreamlitSecretNotFoundError:
                return os.getenv(name, default)
    except ModuleNotFoundError:
        pass

    return os.getenv(name, default)


key = get_secret("GOOGLE_API_KEY")

# Check if the key is loaded correctly
if not key:
    raise ValueError(
        "GOOGLE_API_KEY is not set in the environment variables or Streamlit secrets."
    )

client = genai.Client(api_key=key)


def create_intelligence_briefing(markdown):

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    if local:
        report_path = (
            f"output/reports/{today}.md"
        )

        briefing_path = (
            f"output/briefings/"
            f"IB_{today}.md"
        )

        daily_articles = load_markdown_report(
            report_path
        )
    else:
        daily_articles = markdown

    prompt = load_prompt(
    "prompts/daily_briefing.txt"
    )

    final_prompt = build_prompt(
        prompt,
        daily_articles
    )

    briefing = generate_briefing(
        client,
        final_prompt
    )
    if local:
        save_briefing(
            briefing,
            briefing_path
        )

    upload_daily_briefing(today)


def load_prompt(prompt_path: str) -> str:
    """
    Loads the prompt from the specified file.

    Args:
        prompt_path (str): The path to the file containing the prompt.

    Returns:
        str: The loaded prompt.
    """
    with open(
        prompt_path, 
        'r', 
        encoding='utf-8'
        ) as file:
        return file.read()


def load_markdown_report(report_path: str) -> str:
    """
    Loads the markdown report from the specified file.

    Args:
        report_path (str): The path to the file containing the markdown report.

    Returns:
        str: The loaded markdown report.
    """
    with open(
        report_path,
        "r",
        encoding="utf-8"
    ) as f:

        return f.read()


def build_prompt(
        prompt: str,
        daily_articles: str
) -> str:
    """
    Builds the final prompt by combining the system prompt and the report content.

    Args:
        prompt (str): The prompt to guide the model's behavior.
        daily_articles (str): The content of the daily articles.

    Returns:
        str: The combined prompt.
    """
    return f"""
{prompt}

------------------------------------
Curated Daily Articles:

{daily_articles}
"""

def generate_briefing(
    client,
    prompt: str
) -> str:
    """
    Generates a briefing using the Gemini API.

    Args:
        client: The Google client instance.
        prompt (str): The prompt to guide the model's behavior.

    Returns:
        str: The generated briefing.
    """
    import time
    import logging
    import httpx
    from pathlib import Path

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    max_attempts = 3
    backoff_base = 2

    # Save the prompt to a temporary file for debugging if all attempts fail
    dump_path = Path("output/debug_prompt.txt")
    try:
        dump_path.write_text(prompt, encoding="utf-8")
    except Exception:
        pass

    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Generating briefing (attempt {attempt}/{max_attempts})...")
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
            )

            # Extract and display token usage
            usage = getattr(response, "usage_metadata", None)
            if usage:
                prompt_tokens = getattr(usage, "prompt_token_count", None)
                output_tokens = getattr(usage, "candidates_token_count", None)
                try:
                    total_tokens = (prompt_tokens or 0) + (output_tokens or 0)
                except Exception:
                    total_tokens = None

                logger.info("--- Token Usage ---")
                logger.info(f"Prompt tokens: {prompt_tokens}")
                logger.info(f"Output tokens: {output_tokens}")
                logger.info(f"Total tokens used: {total_tokens}")
                logger.info("-------------------")

            return response.text if getattr(response, "text", None) else "No briefing generated."

        except Exception as e:
            last_exc = e
            # Log detailed info for httpx/httpcore errors
            if isinstance(e, httpx.HTTPError):
                logger.warning(f"HTTP error during generate_content: {e!r}")
            else:
                logger.warning(f"Error during generate_content: {e!r}")

            # If final attempt, raise, otherwise back off and retry
            if attempt == max_attempts:
                logger.error("All attempts to generate briefing failed. Prompt saved to debug_prompt.txt")
                raise

            sleep_seconds = backoff_base ** attempt
            logger.info(f"Retrying after {sleep_seconds}s...")
            time.sleep(sleep_seconds)

    # If loop exits unexpectedly, re-raise last exception
    if last_exc:
        raise last_exc
    return "No briefing generated."


def save_briefing(
    briefing: str,
    output_path: str
):
    """Saves the generated briefing to a specified file.

    Args:
        briefing (str): The generated briefing.
        output_path (str): The path to the file where the briefing will be saved.
    """
    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(briefing)


# summarizer/ai_client.py
import asyncio
import logging

import config.env_ini as env
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config.score_system import BatchEvaluation, SCORING_SYSTEM_PROMPT


logger = logging.getLogger(__name__)

# Set up global client initialization for this module
key = env.get_env_var("GOOGLE_API_KEY")
if not key:
    raise ValueError(
        "GOOGLE_API_KEY is not set in the environment variables or Streamlit secrets."
    )

client = genai.Client(api_key=key)

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash"
]


async def async_evaluate_batch(batch_text: str) -> BatchEvaluation | None:
    """
    Sends a batch of articles to Gemini.
    If a model suffers a temporary 503 overload, it automatically fails over
    to backup models before giving up.
    """
    for model_name in FALLBACK_MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=batch_text,
                config=types.GenerateContentConfig(
                    system_instruction=SCORING_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=BatchEvaluation,
                    temperature=0.1
                ),
            )
            return BatchEvaluation.model_validate_json(response.text)

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
    return None

# summarizer/ai_client.py
import config.env_ini as env
import json
from google import genai
from google.genai import types
from google.genai.errors import APIError
import asyncio
from config.score_system import BatchEvaluation, SCORING_SYSTEM_PROMPT

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
            # Check specifically for a 503 or transient network error
            if api_err.code == 503:
                print(f"⚠️ Model {model_name} is overloaded (503). Attempting fallback...")
                # Optional: pause briefly for a half-second to let things settle
                await asyncio.sleep(0.5)
                continue  # Drops down to the next model in the loop

            if api_err.code == 429:
                print(f"⚠️ Rate limit exceeded for model {model_name} (429). Attempting fallback...")
                await asyncio.sleep(0.5)
                continue
            else:
                print(f"❌ Critical Google API Error ({api_err.code}): {api_err.message}")
                break

        except Exception as e:
            # Captures generic parsing, network, or unknown errors
            print(f"💥 Unexpected system failure on model {model_name}: {e}")
            break

    # If the loop completes and every model failed, return None to keep the pipeline moving
    print("🚨 All fallback models exhausted. Batch skipped.")
    return None
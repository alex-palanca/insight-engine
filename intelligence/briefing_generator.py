import os
from google import genai
from typing import Optional
from google.genai.errors import APIError
import time
from pathlib import Path


FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]

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

# Set up global client initialization for this module
key = get_secret("GOOGLE_API_KEY")
if not key:
    raise ValueError(
        "GOOGLE_API_KEY is not set in the environment variables or Streamlit secrets."
    )

client = genai.Client(api_key=key)


def create_intelligence_briefing(markdown):


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
    
    return briefing

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

    # Save the prompt to a temporary file for debugging if all attempts fail
    dump_path = Path("output/debug_prompt.txt")
    try:
        dump_path.write_text(prompt, encoding="utf-8")
    except Exception:
        pass

    for model_name in FALLBACK_MODELS:
        try:
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            
            return response.text if getattr(response, "text", None) else "No briefing generated."

        except APIError as api_err:
            # Catch transient server overloads
            if api_err.code == 503:
                print(f"⚠️ Model {model_name} is overloaded (503). Attempting fallback...")
                time.sleep(5)
                continue
            else:
                print(f"Google API Error ({api_err.code}): {api_err.message}")
                time.sleep(5)
                continue 

        except Exception as e:
            print(f"Unexpected system failure on model {model_name}: {e}")
            time.sleep(5)
            continue

    print("🚨 All fallback models exhausted. Synthesis failed.")
    return "## Pipeline Error\n\nThe ISOLATE pipeline successfully enriched the data, but the final synthesis models were entirely unavailable due to extreme cloud demand. Please run the pipeline again later."


import os
from dotenv import load_dotenv 
from google import genai
from datetime import datetime
from storage.storage_service import upload_daily_briefing

# Load environment variables from .env file
load_dotenv()
key = os.getenv("GOOGLE_API_KEY")

# Check if the key is loaded correctly
if not key:
    raise ValueError(
        "GOOGLE_API_KEY is not set in the environment variables."
        )

client = genai.Client(api_key=key)


def create_intelligence_briefing():

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    report_path = (
        f"output/reports/{today}.md"
    )

    briefing_path = (
        f"output/briefings/"
        f"IB_{today}.md"
    )

    prompt = load_prompt(
        "prompts/daily_briefing.txt"
    )

    daily_articles = load_markdown_report(
        report_path
    )

    final_prompt = build_prompt(
        prompt,
        daily_articles
    )

    briefing = generate_briefing(
        client,
        final_prompt
    )

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
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text if response.text else "No briefing generated."


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


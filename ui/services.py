import sys
from pathlib import Path
import json

# Ensure the project root is on sys.path so ui imports work from any cwd.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from storage.s3_client import S3Storage as s3
import storage.storage_utils as utils


cloud = s3()


def get_briefing_files():
    files = cloud.list_files("briefings")
    return sorted(files, reverse=True)


def briefing_loader(key):
    return cloud.get_file_content(key)


def get_briefing_date(key):

    filename = key.split("/")[-1]

    return filename.replace(
        "IB_",
        ""
    ).replace(
        ".md",
        ""
    )

def get_markdown_report(date: str) -> str:
    """Fetches the intermediate markdown context for a specific date."""
    try:
        # Using the path we established in our previous pipeline refactor
        return utils.obtain_markdown(date)
    except Exception as e:
        print(f"Error fetching markdown for {date}: {e}")
        return None

def get_raw_articles(date: str) -> list | dict:
    """Fetches and parses the raw JSON articles for a specific date."""
    try:
        content = cloud.get_file_content(f"articles/{date}.json")
        return json.loads(content)
    except Exception as e:
        print(f"Error fetching JSON for {date}: {e}")
        return None
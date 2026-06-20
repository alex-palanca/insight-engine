import sys
from pathlib import Path

# Ensure the project root is on sys.path so ui imports work from any cwd.
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from storage.s3_client import S3Storage as s3


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
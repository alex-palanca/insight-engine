import json
import logging
from datetime import date

from storage.s3_client import S3Storage


today = date.today()
cloud = S3Storage()
logger = logging.getLogger(__name__)


def upload_articles(date: str, content):
    cloud.upload_content(
        content,
        cloud.article_key(date)
    )


def upload_briefing(date: str, file_input):
    cloud.upload_content(
        file_input,
        cloud.briefing_key(date)
    )


def upload_markdown(date: str, content):
    cloud.upload_content(
        content,
        cloud.markdown_key(date)
    )


def obtain_markdown(date: str):
    markdown = cloud.get_file_content(
        cloud.markdown_key(date)
    )
    return markdown


def download_articles(date: str):
    cloud.download_file(
        f"output/articles/{date}.json",
        cloud.article_key(date)
    )


def download_briefing(date: str):
    cloud.download_file(
        f"output/briefings/IB_{date}.md",
        cloud.briefing_key(date)
    )


def save_articles(articles):
    json_articles = json.dumps(articles, indent=2, ensure_ascii=False)

    logger.info("Uploading articles to S3.")
    upload_articles(date.today().isoformat(), json_articles)

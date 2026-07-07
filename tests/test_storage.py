import config.env_ini # noqa: F401
from storage.s3_client import S3Storage


# Test 1: Article key generation
def test_article_key():

    key = S3Storage.article_key("2026-06-21")

    assert key == "articles/2026-06-21.json"


# Test 2: Briefing key generation
def test_briefing_key():

    key = S3Storage.briefing_key("2026-06-21")

    assert key == "briefings/IB_2026-06-21.md"
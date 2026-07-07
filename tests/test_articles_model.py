from datetime import date
import pytest
from models.article import Article


VALID_ARTICLE = {
    "title": "NVIDIA launches Blackwell",
    "link": "https://example.com/article",
    "published": date(2026, 6, 21),
    "source": "Reuters",
    "category": "Technology",
    "summary": "This is a sufficiently long summary. " * 5,
    "source_url": "https://example.com/feed.xml",
}


# Test 1: Valid article creation
def test_article_creation():

    test_article = Article(**VALID_ARTICLE)

    assert test_article.title == "NVIDIA launches Blackwell"
    assert test_article.source == "Reuters"
    assert test_article.category == "Technology"


# Test 2: HTML cleanup
def test_summary_html_is_removed():

    data = VALID_ARTICLE.copy()

    data["summary"] = (
        "<p>Hello <b>World</b></p>"
        + " Very long summary. " * 20
    )

    test_article = Article(**data)

    assert "<p>" not in test_article.summary
    assert "<b>" not in test_article.summary
    assert "Hello World" in test_article.summary


# Test 3: Image tags removed
def test_summary_image_removed():

    data = VALID_ARTICLE.copy()

    data["summary"] = (
        "<img src='image.jpg'>"
        + " Very long summary. " * 20
    )

    test_article = Article(**data)

    assert "<img" not in test_article.summary


# Test 4: HTML entities removed
def test_summary_nbsp_removed():

    data = VALID_ARTICLE.copy()

    data["summary"] = (
        "Hello&nbsp;World"
        + " Very long summary. " * 20
    )

    test_article = Article(**data)

    assert "&nbsp;" not in test_article.summary
    assert "Hello World" in test_article.summary


# Test 5: Reject summaries that are too short
def test_summary_too_short():

    data = VALID_ARTICLE.copy()

    data["summary"] = "Too short"

    with pytest.raises(ValueError):

        Article(**data)


# Test 6: Reject summaries containing invalid markers
def test_invalid_summary_marker():

    data = VALID_ARTICLE.copy()

    data["summary"] = (
        "Read more about this story."
        + " Very long summary. " * 20
    )

    with pytest.raises(ValueError):

        Article(**data)


# Test 7: Reject invalid URLs
def test_invalid_url():

    data = VALID_ARTICLE.copy()

    data["link"] = "not_a_url"

    with pytest.raises(ValueError):

        Article(**data)


# Test 8: Reject invalid publication date
def test_invalid_date():

    data = VALID_ARTICLE.copy()

    data["published"] = "not-a-date"

    with pytest.raises(ValueError):

        Article(**data)


# Test 9: Default tags are empty lists
def test_default_tags():

    test_article = Article(**VALID_ARTICLE)

    assert test_article.source_tags == []
    assert test_article.article_tags == []


# Test 10: Preserve valid summary text
def test_summary_preserved_after_cleaning():

    data = VALID_ARTICLE.copy()

    original = (
        "Artificial Intelligence is transforming healthcare. "
        * 8
    )

    data["summary"] = original

    test_article = Article(**data)

    assert "Artificial Intelligence" in test_article.summary
    assert "healthcare." in test_article.summary

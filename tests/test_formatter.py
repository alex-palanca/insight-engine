import config.env_ini # noqa: F401
from processing.formatter import format_context

VALID_ENRICHED_ARTICLE = {
    "title": "NVIDIA launches Blackwell",
    "category": "Technology",
    "source": "Reuters",
    "link": "https://example.com",
    "score": 95,
    "ai_summary": "This is the AI generated summary.",
    "justification": "High impact AI announcement.",
    "metrics": {
        "immediacy": 9,
        "scale": 10,
        "permanence": 8,
        "reverberance": 9,
        "novelty": 10
    }
}

# Test 1: Empty article list
def test_empty_articles():

    markdown = format_context([])

    assert "Total High-Signal Articles: 0" in markdown


# Test 2: Category header
def test_category_header():

    markdown = format_context([VALID_ENRICHED_ARTICLE])

    assert "## Technology" in markdown


# Test 3: Title appears
def test_article_title():

    markdown = format_context([VALID_ENRICHED_ARTICLE])

    assert "NVIDIA launches Blackwell" in markdown


# Test 4: AI summary appears
def test_ai_summary():

    markdown = format_context([VALID_ENRICHED_ARTICLE])

    assert "This is the AI generated summary." in markdown

# Test 5: Score appears
def test_score():

    markdown = format_context([VALID_ENRICHED_ARTICLE])

    assert "[SCORE: 95/100]" in markdown

# Test 6: Justification appears
def test_justification():

    markdown = format_context([VALID_ENRICHED_ARTICLE])

    assert "High impact AI announcement." in markdown

# Test 7: Metrics rendered
def test_metrics():

    markdown = format_context([VALID_ENRICHED_ARTICLE])

    assert "Immediacy(9)" in markdown
    assert "Scale(10)" in markdown
    assert "Novelty(10)" in markdown

# Test 8: Missing metrics handled
def test_missing_metrics():

    article = VALID_ENRICHED_ARTICLE.copy()

    article["metrics"] = {}

    markdown = format_context([article])

    assert "Metrics:" not in markdown
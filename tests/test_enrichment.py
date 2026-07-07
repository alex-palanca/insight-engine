import asyncio
import importlib
import sys
import types
from unittest.mock import AsyncMock
import config.env_ini # noqa: F401

from config.score_system import ArticleScore, BatchEvaluation


def load_enrichment_module():
    fake_ai_client = types.ModuleType("intelligence.ai_client")

    async def placeholder_async_evaluate_batch(_batch_text: str):
        return None

    fake_ai_client.async_evaluate_batch = placeholder_async_evaluate_batch
    sys.modules["intelligence.ai_client"] = fake_ai_client
    sys.modules.pop("processing.enrichment", None)
    return importlib.import_module("processing.enrichment")


def make_article(title="Example", summary="Fallback summary"):
    return {
        "title": title,
        "link": "https://example.com/article",
        "summary": summary,
        "source": "Reuters",
        "category": "Tech",
    }


class FakeResponse:
    def __init__(self, status, text):
        self.status = status
        self._text = text

    async def text(self):
        return self._text


class FakeRequestContext:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def get(self, _url, timeout=8):
        if self.error:
            raise self.error
        return FakeRequestContext(self.response)


def test_fetch_full_article_uses_scraped_content(monkeypatch):
    enrichment = load_enrichment_module()
    long_text = "word " * 250
    monkeypatch.setattr(enrichment.trafilatura, "extract", lambda _html: long_text)

    article = make_article()
    session = FakeSession(FakeResponse(200, "<html>ok</html>"))

    result = asyncio.run(enrichment.fetch_full_article(session, article))

    assert result["content_to_evaluate"] == long_text
    assert "score" not in result


def test_fetch_full_article_falls_back_for_paywall(monkeypatch):
    enrichment = load_enrichment_module()
    monkeypatch.setattr(
        enrichment.trafilatura,
        "extract",
        lambda _html: "subscribe to read " + ("word " * 250),
    )

    article = make_article(summary="RSS summary fallback")
    session = FakeSession(FakeResponse(200, "<html>blocked</html>"))

    result = asyncio.run(enrichment.fetch_full_article(session, article))

    assert result["content_to_evaluate"] == "RSS summary fallback"


def test_fetch_full_article_falls_back_on_request_error():
    enrichment = load_enrichment_module()
    article = make_article(summary="Fallback after error")
    session = FakeSession(error=RuntimeError("network down"))

    result = asyncio.run(enrichment.fetch_full_article(session, article))

    assert result["content_to_evaluate"] == "Fallback after error"


def test_process_batch_maps_batch_evaluation(monkeypatch):
    enrichment = load_enrichment_module()

    async def fake_async_evaluate_batch(_prompt):
        return BatchEvaluation(
            evaluations=[
                ArticleScore(
                    article_index=1,
                    immediacy=10,
                    scale=11,
                    permanence=12,
                    reverberance=13,
                    novelty=14,
                    justification="High impact.",
                    ai_summary="Dense summary.",
                )
            ]
        )

    monkeypatch.setattr(enrichment, "async_evaluate_batch", fake_async_evaluate_batch)

    batch = [
        {"title": "A", "content_to_evaluate": "text a"},
        {"title": "B", "content_to_evaluate": "text b"},
    ]

    result = asyncio.run(enrichment.process_batch(batch, batch_id=1))

    assert result[0]["score"] == 0
    assert result[0]["ai_summary"] == ""
    assert result[1]["score"] == 60
    assert result[1]["ai_summary"] == "Dense summary."
    assert result[1]["justification"] == "High impact."
    assert result[1]["metrics"] == {
        "immediacy": 10,
        "scale": 11,
        "permanence": 12,
        "reverberance": 13,
        "novelty": 14,
    }


def test_process_batch_keeps_default_fields_when_ai_fails(monkeypatch):
    enrichment = load_enrichment_module()

    async def fake_async_evaluate_batch(_prompt):
        return None

    monkeypatch.setattr(enrichment, "async_evaluate_batch", fake_async_evaluate_batch)

    batch = [{"title": "A", "content_to_evaluate": "text a"}]

    result = asyncio.run(enrichment.process_batch(batch, batch_id=2))

    assert result == [
        {
            "title": "A",
            "content_to_evaluate": "text a",
            "score": 0,
            "ai_summary": "",
            "justification": "",
            "metrics": {},
        }
    ]


def test_enrich_articles_pipeline_batches_rate_limits_and_sorts(monkeypatch):
    enrichment = load_enrichment_module()
    batch_sizes = []

    class FakeClientSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def fake_fetch_full_article(_session, article):
        enriched = article.copy()
        enriched["content_to_evaluate"] = article["summary"]
        return enriched

    async def fake_process_batch(batch, batch_id):
        batch_sizes.append((batch_id, len(batch)))
        result = []
        for index, article in enumerate(batch):
            enriched = article.copy()
            enriched["score"] = batch_id * 10 + index
            enriched["ai_summary"] = f"summary-{batch_id}-{index}"
            enriched["justification"] = f"why-{batch_id}-{index}"
            enriched["metrics"] = {"immediacy": batch_id}
            result.append(enriched)
        return result

    sleep_mock = AsyncMock()

    monkeypatch.setattr(enrichment.aiohttp, "ClientSession", FakeClientSession)
    monkeypatch.setattr(enrichment, "fetch_full_article", fake_fetch_full_article)
    monkeypatch.setattr(enrichment, "process_batch", fake_process_batch)
    monkeypatch.setattr(enrichment.asyncio, "sleep", sleep_mock)
    monkeypatch.setattr(enrichment, "BATCH_SIZE", 2)
    monkeypatch.setattr(enrichment, "RATE_LIMIT_DELAY", 9.5)

    articles = [
        make_article(title="A", summary="sum-a"),
        make_article(title="B", summary="sum-b"),
        make_article(title="C", summary="sum-c"),
    ]

    result = asyncio.run(enrichment.enrich_articles_pipeline(articles))

    assert batch_sizes == [(1, 2), (2, 1)]
    assert [article["score"] for article in result] == [20, 11, 10]
    sleep_mock.assert_awaited_once_with(9.5)


from datetime import datetime
from types import SimpleNamespace
import pytest
import config.env_ini # noqa: F401
import storage.db_service as db_service


class SessionContext:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeInsertOperation:
    def __init__(self, model):
        self.model = model
        self.values_payload = None
        self.conflict_called = False

    def values(self, **kwargs):
        self.values_payload = kwargs
        return self

    def on_conflict_do_nothing(self):
        self.conflict_called = True
        return self


class FakeSourceQuery:
    def __init__(self, results):
        self.results = list(results)

    def filter(self, _expression):
        return self

    def first(self):
        return self.results.pop(0)


class FakeArticleLookupQuery:
    def __init__(self, article):
        self.article = article
        self.filter_by_calls = []

    def filter_by(self, **kwargs):
        self.filter_by_calls.append(kwargs)
        return self

    def first(self):
        return self.article


class FakeGetArticlesQuery:
    def __init__(self, results):
        self.results = results
        self.join_model = None
        self.filter_args = None
        self.ordered = False

    def join(self, model):
        self.join_model = model
        return self

    def filter(self, *args):
        self.filter_args = args
        return self

    def order_by(self, _value):
        self.ordered = True
        return self

    def all(self):
        return self.results


class FakeResetQuery:
    def __init__(self):
        self.updated_with = None
        self.deleted = False

    def update(self, payload):
        self.updated_with = payload

    def delete(self):
        self.deleted = True


class FakeSession:
    def __init__(self, source_results=None, article_lookup=None, query_overrides=None, execute_error=None):
        self.source_query = FakeSourceQuery(source_results or [])
        self.article_lookup_query = FakeArticleLookupQuery(article_lookup)
        self.query_overrides = query_overrides or {}
        self.execute_error = execute_error
        self.added = []
        self.flush_called = False
        self.executed = []
        self.committed = False
        self.rolled_back = False

    def query(self, model):
        if model in self.query_overrides:
            return self.query_overrides[model]
        if model is db_service.Source:
            return self.source_query
        if model is db_service.Article:
            return self.article_lookup_query
        raise AssertionError(f"Unexpected query model: {model}")

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flush_called = True
        if self.added and getattr(self.added[-1], "id", None) is None:
            self.added[-1].id = 99

    def execute(self, op):
        if self.execute_error:
            raise self.execute_error
        self.executed.append(op)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def make_service(session):
    service = db_service.NeonDatabaseService.__new__(db_service.NeonDatabaseService)
    service._SessionMarker = lambda: SessionContext(session)
    return service


def test_save_bronze_data_creates_missing_source_and_normalizes_insert(monkeypatch):
    operations = []

    def fake_insert(model):
        operation = FakeInsertOperation(model)
        operations.append(operation)
        return operation

    session = FakeSession(source_results=[None])
    service = make_service(session)

    monkeypatch.setattr(db_service, "insert", fake_insert)

    service.save_bronze_data(
        [
            {
                "title": "Hello, World!",
                "link": "https://example.com/story/?utm_source=rss&x=1",
                "published": "2026-07-07T00:00:00",
                "article_tags": ["ai"],
                "summary": "summary",
                "source": "BBC",
                "category": "world",
                "source_tags": ["trusted"],
                "source_url": "https://example.com/feed",
            }
        ]
    )

    assert len(session.added) == 1
    assert session.flush_called is True
    assert session.committed is True
    assert len(operations) == 1
    assert operations[0].conflict_called is True
    assert operations[0].values_payload["title"] == "hello world"
    assert operations[0].values_payload["link"] == db_service.normalize_url(
        "https://example.com/story/?utm_source=rss&x=1"
    )
    assert operations[0].values_payload["source_id"] == 99


def test_save_bronze_data_rolls_back_on_insert_error(monkeypatch):
    monkeypatch.setattr(db_service, "insert", lambda model: FakeInsertOperation(model))

    session = FakeSession(
        source_results=[SimpleNamespace(id=7, name="BBC")],
        execute_error=RuntimeError("db write failed"),
    )
    service = make_service(session)

    with pytest.raises(RuntimeError):
        service.save_bronze_data(
            [
                {
                    "title": "Hello",
                    "link": "https://example.com/story",
                    "published": "2026-07-07T00:00:00",
                    "summary": "summary",
                    "source": "BBC",
                    "category": "world",
                    "source_url": "https://example.com/feed",
                }
            ]
        )

    assert session.rolled_back is True
    assert session.committed is False


def test_save_silver_data_updates_matching_article_and_uses_content_id():
    article = SimpleNamespace(
        ai_summary="old",
        score=10,
        metrics={"old": True},
        justification="old why",
        enriched_at=None,
    )
    session = FakeSession(article_lookup=article)
    service = make_service(session)

    service.save_silver_data(
        [
            {
                "title": "Hello, World!",
                "link": "https://example.com/story/?utm_source=rss&x=1",
                "ai_summary": "new summary",
                "score": 88,
                "metrics": {"immediacy": 12},
                "justification": "important",
            }
        ]
    )

    expected_content_id = db_service.generate_article_id(
        db_service.normalize_text("Hello, World!"),
        db_service.normalize_url("https://example.com/story/?utm_source=rss&x=1"),
    )

    assert session.article_lookup_query.filter_by_calls == [{"content_id": expected_content_id}]
    assert article.ai_summary == "new summary"
    assert article.score == 88
    assert article.metrics == {"immediacy": 12}
    assert article.justification == "important"
    assert isinstance(article.enriched_at, datetime)
    assert session.committed is True


def test_save_silver_data_preserves_existing_values_when_fields_are_missing():
    article = SimpleNamespace(
        ai_summary="kept summary",
        score=70,
        metrics={"kept": True},
        justification="kept justification",
        enriched_at=None,
    )
    session = FakeSession(article_lookup=article)
    service = make_service(session)

    service.save_silver_data(
        [
            {
                "title": "Hello",
                "link": "https://example.com/story",
                "score": 90,
            }
        ]
    )

    assert article.ai_summary == "kept summary"
    assert article.score == 90
    assert article.metrics == {"kept": True}
    assert article.justification == "kept justification"


def test_get_articles_maps_rows_to_plain_dicts():
    db_article = SimpleNamespace(
        title="Example",
        link="https://example.com/story",
        published=datetime(2026, 7, 7, 8, 0, 0),
        source=SimpleNamespace(name="Reuters", category="world"),
        ai_summary="summary",
        score=91,
        metrics={"immediacy": 10},
        justification="why",
    )
    query = FakeGetArticlesQuery([db_article])
    session = FakeSession(query_overrides={db_service.Article: query})
    service = make_service(session)

    result = service.get_articles(60)

    assert query.join_model is db_service.Source
    assert query.ordered is True
    assert result == [
        {
            "title": "Example",
            "link": "https://example.com/story",
            "published": "2026-07-07T08:00:00",
            "source": "Reuters",
            "category": "world",
            "ai_summary": "summary",
            "score": 91,
            "metrics": {"immediacy": 10},
            "justification": "why",
        }
    ]


def test_reset_events_clears_article_event_ids_and_deletes_events():
    article_query = FakeResetQuery()
    event_query = FakeResetQuery()
    session = FakeSession(
        query_overrides={
            db_service.Article: article_query,
            db_service.Event: event_query,
        }
    )
    service = make_service(session)

    service.reset_events()

    assert article_query.updated_with == {db_service.Article.event_id: None}
    assert event_query.deleted is True
    assert session.committed is True

# ISOLATE

ISOLATE is a lightweight intelligence pipeline that collects news from RSS feeds, enriches articles with AI, clusters related stories into events, and produces daily briefing outputs.

## What it does

- Ingests articles from YAML-configured feeds
- Extracts and cleans article content
- Enriches articles with Gemini-based summaries and scores
- Groups related stories into event clusters
- Formats the best content into markdown reports and briefing text
- Stores results in a database and optional cloud storage

## Current architecture

- Ingestion lives in the ingestion package
- Processing and enrichment logic lives in processing
- Gemini prompts and generation logic live in intelligence
- Article and event persistence uses SQLAlchemy with Neon/Postgres
- Output delivery uses storage helpers and a simple Streamlit UI
- Scheduled runs are supported through GitHub Actions

## Quick start

```bash
pip install -r requirements.txt
python main.py ingest
python main.py enrich
python main.py events_processing
python main.py format
python main.py synthesize
```

The main pipeline entry point is main.py.
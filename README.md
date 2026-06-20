# DAILY BRIEFER

A personal intelligence briefing system that collects articles from curated RSS feeds, saves them to JSON, generates markdown reports, and creates AI-powered intelligence briefings.

The long-term goal is to create an AI-powered assistant that filters information noise and produces concise, high-signal intelligence briefings focused on personalized curated sources.

## Current Features

* RSS feed collection from YAML-configured sources
* Per-category and per-source article limits
* Article categorization and summary capture
* JSON storage of collected articles
* Daily markdown report generation
* AI-generated intelligence briefings using Google Gemini
* Streamlit UI for viewing briefings

## Project Structure

* `main.py` - CLI runner for collection, report generation, and briefing creation
* `collector/rss_collector.py` - RSS collection and JSON output
* `reporter/report_generator.py` - Markdown report generation
* `summarizer/briefing_generator.py` - AI briefing generation using Gemini
* `ui/app.py` - Streamlit app for viewing briefings
* `config/feeds.example.yaml` - Sample feed configuration
* `.env.example` - Required environment variables template
* `output/articles/` - Collected article JSON files
* `output/reports/` - Generated daily markdown reports
* `output/briefings/` - Generated intelligence briefings

## Requirements

Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Setup

1. Copy and configure environment variables:

```bash
copy .env.example .env
```

2. Set `GOOGLE_API_KEY` in `.env`.

3. Copy `config/feeds.example.yaml` to `config/feeds.yaml` and customize feed sources.

## Usage

Run the full process from the command line:

```bash
python main.py
```

Run the Streamlit UI:

```bash
streamlit run ui/app.py
```

## Feed Configuration

Feeds are defined in `config/feeds.yaml` with category groups and source entries. Example format:

```yaml
technology:
  - name: Hacker News
    url: https://hnrss.org/frontpage
business:
  - name: Financial Times
    url: https://www.ft.com/?format=rss
```

## Environment Variables

Required variables:

* `GOOGLE_API_KEY` - Google API key used by the Gemini client

## Notes

* The app saves raw collected articles in `output/articles/daily_articles.json`.
* Daily markdown reports are generated in `output/reports/`.
* AI-generated briefings are saved in `output/briefings/` with filenames like `IB_YYYY-MM-DD.md`.
* `.env` is excluded from git via `.gitignore` and should never be committed.

## Current Development Stage

### Implemented

* RSS feed ingestion
* YAML feed configuration
* Per-category article limits
* Per-source article limits
* Article storage in JSON
* Markdown report generation
* AI intelligence briefing generation
* Streamlit briefing viewer

### Next Improvements

* Better feed error handling and retries
* More robust summary extraction
* Search and filtering in the Streamlit UI
* Settings for feed limits and report formatting
* Support for additional AI prompt templates

## Motivation

Most news platforms optimize for engagement instead of signal. This project aims to collect information from trusted sources, summarize what matters, and present concise briefings for faster awareness and decision-making.

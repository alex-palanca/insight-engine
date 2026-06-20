# DAILY BRIEFER

A personal intelligence briefing system that collects articles from curated RSS feeds, saves them to JSON, generates markdown reports, and creates AI-powered intelligence briefings.

The long-term goal is to create an AI-powered assistant that filters information noise and produces concise, high-signal intelligence briefings focused on personalized curated sources.

## Current Features

* RSS feed collection from YAML-configured sources
* Per-category and per-source article limits
* Article categorization and summary capture
* Date-based JSON storage of collected articles (YYYY-MM-DD.json format)
* S3 integration for article and briefing storage
* Daily markdown report generation
* AI-generated intelligence briefings using Google Gemini
* Streamlit UI for viewing briefings with historical access
* Local based upload of articles and briefings to S3

## Project Structure

* `main.py` - CLI runner for collection, report generation, and briefing creation
* `collector/rss_collector.py` - RSS collection with date-based JSON output and S3 upload
* `reporter/report_generator.py` - Markdown report generation
* `summarizer/briefing_generator.py` - AI briefing generation using Gemini
* `ui/app.py` - Streamlit app for viewing today's and historical briefings
* `ui/services.py` - UI service layer for S3 retrieval and file operations
* `storage/s3_client.py` - S3 client for cloud storage
* `storage/storage_service.py` - Storage service abstraction layer
* `config/feeds.example.yaml` - Sample feed configuration
* `.env.example` - Required environment variables template
* `output/articles/` - Collected article JSON files (named by date: YYYY-MM-DD.json)
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

2. Set required environment variables in `.env`:
   - `GOOGLE_API_KEY` - Google API key for Gemini
   - `AWS_ACCESS_KEY_ID` - AWS credentials for S3
   - `AWS_SECRET_ACCESS_KEY` - AWS credentials for S3
   - `AWS_S3_BUCKET` - S3 bucket name

3. Copy `config/feeds.example.yaml` to `config/feeds.yaml` and customize feed sources.

## Usage

### Run the full collection and briefing pipeline:

```bash
python main.py
```

This will:
1. Collect articles from configured RSS feeds
2. Save articles to `output/articles/YYYY-MM-DD.json` and upload to S3
3. Generate a markdown report
4. Generate an AI-powered intelligence briefing
5. Upload briefing to S3

### View briefings in the Streamlit UI:

```bash
streamlit run ui/app.py
```

The UI allows you to:
- View today's intelligence briefing
- Browse historical briefings
- Filter briefings by date

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

Required variables in `.env`:

* `GOOGLE_API_KEY` - Google API key for Gemini
* `AWS_ACCESS_KEY_ID` - AWS access key
* `AWS_SECRET_ACCESS_KEY` - AWS secret key
* `AWS_S3_BUCKET` - S3 bucket name for storage

## Architecture Notes

* Articles are collected with per-category limits (default: 30) and per-source limits (default: 5)
* Articles are saved locally to `output/articles/{date}.json` and uploaded to S3
* The Streamlit UI retrieves briefings from S3 for viewing
* All imports use project-root path resolution for flexible execution from any working directory
* `.env` is excluded from git via `.gitignore` and should never be committed

## Recent Changes

* Date-based article filenames (YYYY-MM-DD.json format) for better organization
* S3 integration for cloud storage of articles and briefings
* Fixed import paths to support execution from any working directory
* Removed unused S3 imports from main.py
* Streamlit UI now with proper module imports and S3 integration

## Current Development Stage

### Implemented

* RSS feed ingestion with category support
* YAML feed configuration
* Per-category article limits
* Per-source article limits
* Date-based article storage in JSON
* S3 upload of articles and briefings
* Markdown report generation
* AI intelligence briefing generation with Gemini
* Streamlit UI with historical briefing browsing
* Proper import path resolution for flexible execution

### Known Issues

* Pylance linting warnings about import order (style-only, code is functional)
* Requires AWS credentials for S3 operations

* Streamlit briefing viewer

### Next Improvements

* Better feed error handling and retries
* More robust summary extraction
* Search and filtering in the Streamlit UI
* Settings for feed limits and report formatting
* Support for additional AI prompt templates

## Motivation

Most news platforms optimize for engagement instead of signal. This project aims to collect information from trusted sources, summarize what matters, and present concise briefings for faster awareness and decision-making.

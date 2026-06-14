# DAILY BRIEFER

A personal intelligence briefing system that collects articles from curated RSS feeds and generates structured daily reports.

The long-term goal is to create an AI-powered assistant that filters information noise and produces concise, high-signal intelligence briefings focused on personalized curated sources.

## Current Features

* RSS feed collection
* Configurable feed sources
* Article categorization
* JSON article storage
* Markdown report generation
* Daily timestamped reports in .md


## How It Works

```text
RSS Feeds
    ↓
Article Collection
    ↓
JSON Storage
    ↓
Markdown Report Generation
```

Example output:

```text
output/reports/2026-06-14.md
```

## Configuration

Feed sources are configured externally through JSON files.

The repository contains:

```text
config/feeds.example.json
```

Create your own:

```text
config/feeds.json
```

and customize the sources as desired.

## Current Development Stage

### Implemented

* RSS feed ingestion
* External feed configuration
* Article categorization
* JSON article storage
* Markdown report generation
* Daily report archiving

## Roadmap

### Intelligence Generation

* AI-powered article summarization
* Executive briefing generation
* Multi-source synthesis
* Key development identification
* Long-term impact analysis

### Information Quality

* Duplicate story detection
* Source reliability assessment
* Importance and relevance scoring
* Noise reduction and filtering

### Knowledge Management

* Historical archive
* Search capabilities
* Topic tracking
* Trend identification
* Cross-reference discovery

### Personalization

* Interest-based ranking
* Personalized briefings
* Adaptive content selection
* User preference learning

### Delivery & Accessibility

* Automated report generation
* Mobile-friendly consumption
* Notification and delivery channels
* Cloud deployment options

### Advanced Capabilities

* Semantic search
* Research assistant features
* Event clustering
* Knowledge graph exploration
* Long-term trend analysis

## Motivation

Most news platforms optimize for engagement, not understanding.

Keeping up with developments in technology, economics, geopolitics, and science often requires reading dozens of articles from multiple sources every day.

This project aims to build a personal intelligence briefing system that collects information from trusted sources, filters irrelevant content, and ultimately delivers concise, high-signal reports focused on developments that are likely to matter in the short and long term.

The objective is simple: spend less time consuming news and more time understanding the world.

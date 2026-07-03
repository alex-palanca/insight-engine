# ISOLATE 📡

> **From Information to Intelligence.** > ISOLATE is a personal intelligence platform designed to extract high-density signal from high-volume noise using asynchronous data engineering and LLM Map-Reduce patterns.

Most news platforms optimize for engagement. ISOLATE optimizes for consequence. It autonomously ingests hundreds of global sources, mathematically scores them using intelligence community frameworks, and synthesizes the highest-value data into an executive briefing. See ROADMAP.md for planned future features.

## 🏗 Architecture

ISOLATE operates on a strict **Map-Reduce** pipeline:

1. **Ingestion:** Parses custom RSS feeds configured via YAML.
2. **Enrichment (The Map Phase):** - Uses `aiohttp` and `trafilatura` for highly concurrent, non-blocking article extraction.
   - Implements **Graceful Degradation**: If a site uses anti-bot protection or paywalls, the system autonomously falls back to RSS summaries.
3. **Scoring & Evaluation:** - Batches articles to respect API rate limits and optimize LLM context windows.
   - Uses **Structured Outputs (Pydantic)** to force Gemini Flash to evaluate articles on a strict 100-point rubric: *Immediacy, Scale, Permanence, Reverberance, and Novelty*.
   - Aggressively filters out any data scoring below 60/100.
4. **Synthesis (The Reduce Phase):** Compiles the mathematically filtered data into dense, highly contextual Markdown reports.
5. **Delivery:** Stores artifacts in AWS S3 and serves them via a modern Streamlit web dashboard.

## ⚙️ Tech Stack

* **Core:** Python 3.12+, `asyncio` (Event-driven concurrency)
* **AI/LLM:** Google GenAI SDK (Gemini 2.5 Flash / Flash-Lite), `pydantic` (Schema enforcement)
* **Data Extraction:** `aiohttp`, `trafilatura`, `feedparser`
* **Infrastructure:** AWS S3 (`boto3`), GitHub Actions (CRON automation)
* **UI:** Streamlit

## 🚀 Quick Start

1. **Clone & Install**
   ```bash
   pip install -r requirements.txt
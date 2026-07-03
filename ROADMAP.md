# ISOLATE - Future Improvements Roadmap

This document outlines the planned technical and product improvements for ISOLATE, ordered chronologically from immediate foundational updates to long-term advanced features.

## Phase 1: Short-Term (Foundations & Best Practices)
* **`settings.yaml` Integration:** Move ML hyperparameters (min_df, max_df) and pipeline configurations out of the code and into a dedicated configuration file.
* **Documentation & Comments:** Standardize docstrings across all modules and add inline comments for complex mathematical or architectural logic (e.g., the TF-IDF and NetworkX implementations).
* **Cloud-Based Logging:** Implement robust logging (e.g., pushing logs to AWS CloudWatch). Ensure that when a step fails, the exact error stack trace is safely stored in the cloud before the pipeline gracefully continues or terminates.

## Phase 2: Medium-Term (Architecture & Scalability)
* **Containerization (Docker):** Dockerize the application to ensure consistency across environments and simplify future cloud deployments.
* **FastAPI Backend:** Decouple the backend logic from the CLI/Streamlit apps by wrapping the core engine in a FastAPI service. This will serve as the backbone for the UI and external integrations.
* **Frontend Migration (Vercel):** Migrate or deploy the Streamlit (or a future React/Next.js) frontend to Vercel for better performance, edge delivery, and professional portfolio presentation.
* **AWS Serverless Migration:** * Replace the GitHub Actions cron job with **Amazon EventBridge**.
  * Migrate compute to **AWS Lambda**.
  * Orchestrate the multi-step pipeline (Ingest -> Enrich -> Cluster -> Briefing) using **AWS Step Functions**.

## Phase 3: Long-Term (Advanced Intelligence & AI)
* **Temporal Intelligence (Past Context):** Upgrade the LLM prompts and retrieval system to reference past events and briefings. This allows the system to say, *"Following up on yesterday's development..."* or track a story's evolution over weeks.
* **Chatbot Capabilities:** Implement a conversational RAG (Retrieval-Augmented Generation) interface, allowing the user to "talk" to their intelligence database, ask questions about specific events, and generate custom ad-hoc reports.
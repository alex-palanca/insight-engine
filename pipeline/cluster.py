from processing import event_enrichment
import asyncio

def cluster():
    asyncio.run(event_enrichment.enrich_events_pipeline(similarity_threshold=0.375, max_df=0.85, min_df=2))
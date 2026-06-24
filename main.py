import ingestion.rss_collector as rss_collector
from processing import formatter
from intelligence import briefing_generator
from storage import storage_utils as storage
import config
from datetime import datetime

today = datetime.now().strftime(
        "%Y-%m-%d"
    )

def main():
    # News sources to collect RSS feeds from
    feeds = config.feed_loader.load_feeds() 
    print("Starting article collection...")
    cleaned_articles = rss_collector.collect_articles(feeds,200,50)

    print("Saving cleaned articles...")
    storage.save_articles(cleaned_articles)
    
    print("Formatting articles...")
    markdown = formatter.format_context(cleaned_articles)
    print(markdown)

    print("Generating IB report...")
    briefing = briefing_generator.create_intelligence_briefing(markdown)
    print("Saving Intelligence Briefing...")
    storage.upload_briefing(today,briefing)

    print("Finished successfully.")

if __name__ == "__main__":
    # News sources to collect RSS feeds from
    feeds = config.feed_loader.load_feeds() 
    print("Starting article collection...")
    cleaned_articles = rss_collector.collect_articles(feeds,200,50)

    print("Saving cleaned articles...")
    storage.save_articles(cleaned_articles)

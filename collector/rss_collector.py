import feedparser
import config.feed_loader
from storage.storage_service import upload_daily_articles
import json
from datetime import date

# Maximum number of articles to collect per category
MAX_ARTICLES_PER_CATEGORY = 30
# Maximum number of articles to collect per source/feed
MAX_ARTICLES_PER_SOURCE = 5


def collect_articles():
    # News sources to collect RSS feeds from
    feeds = config.feed_loader.load_feeds() 

    articles = []
    category_counts = {}

    for category,category_feeds in feeds.items():

        category_counts[category] = 0

        # Stop early if we've already reached the per-category limit
        if category_counts[category] >= MAX_ARTICLES_PER_CATEGORY:
            continue

        # Error handling for feed parsing by source
        for feed_info in category_feeds:

            # If we've reached the limit for this category, stop processing more feeds
            if category_counts[category] >= MAX_ARTICLES_PER_CATEGORY:
                break
            
            try:
                feed_url = feed_info["url"]

                parsed_feed = feedparser.parse(feed_url)

                # Track how many articles we've taken from this source
                source_count = 0

                for entry in parsed_feed.entries:

                    # Respect both per-category and per-source limits
                    if category_counts[category] >= MAX_ARTICLES_PER_CATEGORY:
                        break
                    if source_count >= MAX_ARTICLES_PER_SOURCE:
                        break

                    article = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published", "Unknown"),
                        "source": feed_info["name"],
                        "category": category,
                        "summary": entry.get("summary", "No summary available")
                    }

                    articles.append(article)

                    category_counts[category] += 1
                    source_count += 1

            except Exception as e:
                print(f"Error collecting articles from {feed_url}: {e}")
       

    print(f"\nCollected {len(articles)} articles total\n")

    for category, count in category_counts.items():
        print(f"{category}: {count}")

    return articles

def save_articles(articles):

    filename = f"output/articles/{date.today().isoformat()}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    print("Uploading articles to S3...")
    upload_daily_articles(date.today().isoformat())

    print(f"Saved {len(articles)} articles to {filename}")
        
            


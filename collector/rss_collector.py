import feedparser
import config.feed_loader
import storage.storage_service as cloud
import json
import re
from datetime import date

# Define Local or Remote 
local = 1

# Maximum number of articles to collect per category
MAX_ARTICLES_PER_CATEGORY = 200
# Maximum number of articles to collect per source/feed
MAX_ARTICLES_PER_SOURCE = 30
# Minimum length required for a valid article summary
MIN_SUMMARY_LENGTH = 100

# Invalid summary markers to filter out low-quality content
INVALID_SUMMARY_MARKERS = [
    "no summary available",
    "summary unavailable",
    "unable to retrieve summary",
    "read more",
    "continue reading",
    "click here",
    # common metadata blocks from aggregators (Article/Comments/Points blocks)
    "article url:",
    "comments url:",
    "points:",
    "# comments",
    "source:",
    "url:",
    "Link:",
    # URLs and tracking
    "http://",
    "https://",
    "www.",
    "utm_",
    # social / external hosts
    "youtube.com",
    "vimeo.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "t.co",
    "facebook.com",
    "github.com",
    "news.ycombinator.com",
    # HTML / embed / image markers
    "<img",
    "<iframe",
    "<video",
    "src=",
    "href=",
    "data:image/",
    "&",
    # promotional / commercial noise
    "promo",
    "promo code",
    "coupon",
    "coupon code",
    "discount",
    "% off",
    "deal",
    "sale",
    "sponsored",
    "ad:",
    "buy now",
    "shop",
    "subscribe",
    "sign up",
    "newsletter",
    # media labels / podcast/video boilerplate
    "video",
    "audio",
    "podcast",
    "livestream",
    "gallery",
    "photo",
    
]



def clean_summary(summary: str) -> str:
    # Remove HTML tags and image references
    cleaned = re.sub(r'<img[^>]*>', '', summary, flags=re.IGNORECASE)
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    cleaned = cleaned.replace('&nbsp;', ' ').strip()
    return cleaned


def is_valid_summary(summary: str) -> bool:
    # Check if the summary is valid based on length
    if not summary:
        return False

    normalized = summary.strip().lower()
    if len(normalized) < MIN_SUMMARY_LENGTH:
        return False
    
    if any(marker in normalized for marker in INVALID_SUMMARY_MARKERS):
        return False

    return True

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

                    raw_summary = entry.get("summary", "")
                    cleaned_summary = clean_summary(raw_summary)
                    if not is_valid_summary(cleaned_summary):
                        continue

                    article = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published", "Unknown"),
                        "source": feed_info["name"],
                        "category": category,
                        "summary": cleaned_summary
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

    json_articles = json.dumps(articles, indent=2, ensure_ascii=False)

    if local != 0:
        filename = f"output/articles/{date.today().isoformat()}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(articles,f, indent=2, ensure_ascii=False)
            

    print("Uploading articles to S3...")
    cloud.upload_articles(date.today().isoformat(),json_articles)

    print(f"Saved {len(articles)} articles to {filename}")
        
            


import feedparser
from datetime import date

# Define Today's date
today = date.today()


def collect_articles(
        feeds: dict,
        max_per_category: int,
        max_per_source: int
) -> list:

    raw_articles = []
    category_counts = {}

    for category,category_feeds in feeds.items():

        category_counts[category] = 0

        # Stop early if we've already reached the per-category limit
        if category_counts[category] >= max_per_category:
            continue

        # Error handling for feed parsing by source
        for feed_info in category_feeds:

            # If we've reached the limit for this category, stop processing more feeds
            if category_counts[category] >= max_per_category:
                break
            
            try:
                feed_url = feed_info["url"]

                parsed_feed = feedparser.parse(feed_url)

                # Track how many articles we've taken from this source
                source_count = 0

                for entry in parsed_feed.entries:

                    # Respect both per-category and per-source limits
                    if category_counts[category] >= max_per_category:
                        break
                    if source_count >= max_per_source:
                        break

                    # Filter outdated using feedparser's built-in parsed date tuple
                    # (Year, Month, Day, Hour, Minute, Second, Weekday, Julian Day, DST)
                    if not hasattr(entry, 'published_parsed') or entry.published_parsed is None:
                        continue
                    
                    entry_year = entry.published_parsed[0]
                    entry_month = entry.published_parsed[1]
                    entry_day = entry.published_parsed[2]

                    # Only accept articles published exactly today
                    if entry_year != today.year or entry_month != today.month or entry_day != today.day:
                        continue

                    article = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published", "Unknown"),
                        "source": feed_info["name"],
                        "category": category,
                        "summary": entry.get("summary", "")
                    }

                    raw_articles.append(article)
                    category_counts[category] += 1
                    source_count += 1
                print(f"{source_count} articles collected from {feed_info['name']}")
            except Exception as e:
                print(f"Error collecting articles from {feed_url}: {e}")
       

    print(f"\nCollected {len(raw_articles)} articles total\n")
    for category, count in category_counts.items():
        print(f"{category}: {count}")

    return raw_articles
        
            


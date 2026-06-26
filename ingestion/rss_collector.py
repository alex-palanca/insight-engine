import feedparser
from datetime import datetime, timedelta, time, timezone
from pydantic import ValidationError
from models.article import Article


now_utc = datetime.now(timezone.utc)
yesterday_utc = now_utc - timedelta(days=1)    
threshold_utc = datetime.combine(yesterday_utc.date(), time(15, 0, 0))


def collect_articles(
        feeds: dict,
        max_per_category: int,
        max_per_source: int
) -> list:

    raw_articles = []
    category_counts = {}

    for category,category_feeds in feeds.items():

        category_counts[category] = 0

        if category_counts[category] >= max_per_category:
            continue

        for feed_info in category_feeds:

            if category_counts[category] >= max_per_category:
                break
            
            try:
                feed_url = feed_info["url"]
                parsed_feed = feedparser.parse(feed_url)

                source_count = 0

                for entry in parsed_feed.entries:

                    # Respect both per-category and per-source limits
                    if category_counts[category] >= max_per_category:
                        break
                    if source_count >= max_per_source:
                        break

                    # Filter outdated using feedparser's built-in parsed date tuple
                    if not hasattr(entry, 'published_parsed') or entry.published_parsed is None:
                        # Fallback
                        if hasattr(entry, 'updated_parsed') and entry.updated_parsed is not None:
                                entry.published_parsed = entry.updated_parsed
                        else:
                            continue
                    
                    entry_utc = datetime(*entry.published_parsed[:6])

                    if entry_utc < threshold_utc:
                        continue                 

                    article_date = entry_utc.date()


                    yaml_tags = feed_info.get("source_tags",[])

                    native_tags = []
                    if hasattr(entry, 'tags'):
                        for t in entry.tags:
                            if hasattr(t, 'term'):
                                # Standardize the publisher's tags: lowercase and replace spaces
                                clean_tag = t.term.lower().replace(" ", "_")
                                native_tags.append(clean_tag)
    
                    native_tags = list(set(native_tags))

                    try:

                        # Article model built and validated
                        article = Article(
                                title=entry.get("title", "No Title"),
                                link=entry.get("link", "http://invalid"),
                                published=article_date,
                                source=feed_info["name"],
                                category=category,
                                source_tags=yaml_tags, 
                                article_tags=native_tags,
                                summary=entry.get("summary", "")
                        )

                        raw_articles.append(article.model_dump(mode='json'))

                        category_counts[category] += 1
                        source_count += 1
                
                    except ValidationError as e:
                        # The data contract was violated
                        continue
            
                print(f"{source_count} articles collected from {feed_info['name']}")
            except Exception as e:
                print(f"Error collecting articles from {feed_url}: {e}")
       

    print(f"\nCollected {len(raw_articles)} articles total\n")
    for category, count in category_counts.items():
        print(f"{category}: {count}")

    return raw_articles
        
            


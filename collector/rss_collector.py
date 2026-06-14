import feedparser
import config.feed_loader
import json

    
def collect_articles():
    # News sources to collect RSS feeds from
    feeds = config.feed_loader.load_feeds() 

    articles = []
    category_counts = {}

    for category,category_feeds in feeds.items():

        category_counts[category] = 0

        #Error handling for feed parsing by source
        for feed_info in category_feeds:
            
            try:
                feed_url = feed_info["url"]

                parsed_feed = feedparser.parse(feed_url)

                for entry in parsed_feed.entries:

                    article = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published", "Unknown"),
                        "source": feed_info["name"],
                        "category": category
                    }

                    articles.append(article)

                    category_counts[category] += 1

            except Exception as e:
                print(f"Error collecting articles from {feed_url}: {e}")
       

    print(f"\nCollected {len(articles)} articles total\n")

    for category, count in category_counts.items():
        print(f"{category}: {count}")

    return articles

def save_articles(articles):

    with open(
        "output/articles/daily_articles.json",
        "w",
        encoding="utf-8"
    ) as f:
        
        json.dump(
            articles,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved {len(articles)} articles to output/articles/daily_articles.json")
        
            


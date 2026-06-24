# reporter/report_generator.py
from datetime import datetime
from config.feed_loader import load_feeds

feeds = load_feeds()
category_order = list(feeds.keys())

def format_context(articles):
    """
    Acts as a pure data formatter. Takes enriched JSON and returns 
    a highly-dense Markdown string for the Synthesizer LLM. 
    Does NOT save to disk.
    """
    date = datetime.now().strftime("%Y-%m-%d")
    print("Formatting enriched data in-memory...")

    grouped_articles = {}
    for article in articles:
        category = article.get("category", "uncategorized")
        if category not in grouped_articles:
            grouped_articles[category] = []
        grouped_articles[category].append(article)

    markdown = f"# Enriched Intelligence Data ({date})\n\n"
    markdown += f"Total High-Signal Articles: {len(articles)}\n\n"

    all_categories = category_order.copy()
    for category in grouped_articles.keys():
        if category not in all_categories:
            all_categories.append(category)

    for category in all_categories:
        if category not in grouped_articles:
            continue

        category_articles = grouped_articles[category]
        category_articles.sort(key=lambda x: x.get('score', 0), reverse=True)

        markdown += f"## {category.title()} ({len(category_articles)} articles)\n\n"

        for article in category_articles:
            score = article.get('score', 0)
            metrics = article.get('metrics', {})
            
            markdown += f"### {article.get('title', 'Untitled')} [SCORE: {score}/100]\n"
            markdown += f"- **Source:** {article.get('source', 'Unknown')} | **Link:** {article.get('link', '')}\n"
            markdown += f"- **AI Summary:**\n{article.get('ai_summary', 'N/A')}\n"
            markdown += f"- **Justification:** {article.get('justification', 'N/A')}\n"
            
            if metrics:
                markdown += (
                    f"- **Metrics:** Immediacy({metrics.get('immediacy', 0)}), "
                    f"Scale({metrics.get('scale', 0)}), "
                    f"Permanence({metrics.get('permanence', 0)}), "
                    f"Reverberance({metrics.get('reverberance', 0)}), "
                    f"Novelty({metrics.get('novelty', 0)})\n"
                )
            markdown += "\n---\n\n"

    return markdown
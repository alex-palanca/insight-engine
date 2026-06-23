from datetime import datetime
from config.feed_loader import load_feeds

date = datetime.now().strftime("%Y-%m-%d")

# Initial categorization order based on the feeds.yaml configuration
feeds = load_feeds()
category_order = list(feeds.keys())


def format_context(enriched_articles: list) -> str:
    """
    Generates a markdown report grouped by category.

    Args:
        enriched_articles (list): List of article dictionaries.
    """
    if not enriched_articles:
        return "No articles available"

    print("Formatting articles to markdown...")

    # 1. Group articles by category for better LLM context structure
    grouped_articles = {}
    for article in enriched_articles:
        # FIX: Changed from article.category.title() to dictionary lookup .get()
        category_raw = article.get("category", "uncategorized")
        category = category_raw.title()
        
        if category not in grouped_articles:
            grouped_articles[category] = []
        grouped_articles[category].append(article)

    # Report header
    markdown = f"# Daily Briefer Report ({date})\n\n"
    markdown += f"Collected Articles: {len(enriched_articles)}\n\n"

    markdown += "| Category | Count |\n"
    markdown += "|----------|-------|\n"

    # Summary table
    for category in category_order:
        count = len(grouped_articles.get(category.title(), []))
        markdown += f"| {category.title()} | {count} |\n"

    # Include any unexpected categories
    for category in grouped_articles:
        if category.lower() not in category_order:
            count = len(grouped_articles[category])
            markdown += f"| {category} | {count} |\n"

    markdown += "\n---\n\n"

    # Main content (Loop through categories explicitly ordered)
    for category_name in category_order:
        category = category_name.title()

        if category not in grouped_articles:
            continue

        category_articles = grouped_articles[category]

        markdown += (
            f"## {category} "
            f"({len(category_articles)} articles)\n\n"
        )

        for article in category_articles:
            markdown += f"### {article.get('title', 'No Title')}\n"
            markdown += f"- Source: {article.get('source', 'Unknown')}\n"
            markdown += f"- Summary: {article.get('summary', 'No summary available')}\n"
            markdown += f"- Published: {article.get('published', 'Unknown')}\n"
            markdown += f"- Link: [{article.get('link', '')}]({article.get('link', '')})\n\n"
        markdown += "---\n\n"

    # Handle categories not defined in CATEGORY_ORDER
    for category, category_articles in grouped_articles.items():
        if category.lower() in category_order:
            continue

        markdown += (
            f"## {category} "
            f"({len(category_articles)} articles)\n\n"
        )

        for article in category_articles:
            markdown += f"### {article.get('title', 'No Title')}\n"
            markdown += f"- Source: {article.get('source', 'Unknown')}\n"       
            markdown += f"- Summary: {article.get('summary', 'No summary available')}\n"
            markdown += f"- Published: {article.get('published', 'Unknown')}\n"
            markdown += f"- Link: [{article.get('link', '')}]({article.get('link', '')})\n\n"

        markdown += "---\n\n"


    print(f"Formatted {len(enriched_articles)} articles.")

    return markdown
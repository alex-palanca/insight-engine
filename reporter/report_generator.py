from datetime import datetime
from config.feed_loader import load_feeds

# Initial categorization order based on the feeds.yaml configuration
feeds = load_feeds()
category_order = list(feeds.keys())


def generate_report(articles):
    """
    Generates a markdown report grouped by category.

    Args:
        articles (list): List of article dictionaries.
    """

    date = datetime.now().strftime("%Y-%m-%d")

    print("Generating report...")

    # Group articles by category
    grouped_articles = {}

    for article in articles:
        category = article.get("category", "uncategorized")

        if category not in grouped_articles:
            grouped_articles[category] = []

        grouped_articles[category].append(article)

    # Report header
    markdown = f"# Daily Briefer Report ({date})\n\n"

    markdown += f"Collected Articles: {len(articles)}\n\n"

    markdown += "| Category | Count |\n"
    markdown += "|----------|-------|\n"

    # Summary table
    for category in category_order:
        count = len(grouped_articles.get(category, []))
        markdown += f"| {category.title()} | {count} |\n"

    # Include any unexpected categories
    for category in grouped_articles:
        if category not in category_order:
            count = len(grouped_articles[category])
            markdown += f"| {category.title()} | {count} |\n"

    markdown += "\n---\n\n"

    # Main content
    for category in category_order:

        if category not in grouped_articles:
            continue

        category_articles = grouped_articles[category]

        markdown += (
            f"## {category.title()} "
            f"({len(category_articles)} articles)\n\n"
        )

        for article in category_articles:

            markdown += f"### {article['title']}\n"

            markdown += (
                f"- Source: {article.get('source', 'Unknown')}\n"
            )

            markdown += (
                f"- summary: {article.get('summary', 'No summary available')}\n"
            )

            markdown += (
                f"- Published: "
                f"{article.get('published', 'Unknown')}\n"
            )

            markdown += (
                f"- Link: "
                f"[{article['link']}]({article['link']})\n\n"
            )

        markdown += "---\n\n"

    # Handle categories not defined in CATEGORY_ORDER
    for category, category_articles in grouped_articles.items():

        if category in category_order:
            continue

        markdown += (
            f"## {category.title()} "
            f"({len(category_articles)} articles)\n\n"
        )

        for article in category_articles:

            markdown += f"### {article['title']}\n"

            markdown += (
                f"- Source: {article.get('source', 'Unknown')}\n"
            )

            markdown += (
                f"- Published: "
                f"{article.get('published', 'Unknown')}\n"
            )

            markdown += (
                f"- Link: "
                f"[{article['link']}]({article['link']})\n\n"
            )

        markdown += "---\n\n"

    # Save report
    report_path = f"output/reports/{date}.md"

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(markdown)

    print(
        f"Report generated successfully: "
        f"{report_path}"
    )

    print(
        f"Processed {len(articles)} articles."
    )
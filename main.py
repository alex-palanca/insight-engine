import collector.rss_collector as rss_collector
import reporter.report_generator as report_generator
from summarizer import briefing_generator


def main():
    
    print("Starting article collection...")
    articles = rss_collector.collect_articles()

    print("Saving articles to markdown report...")
    rss_collector.save_articles(articles)
    #"""""
    print("Generating preliminary report...")
    report_generator.generate_report(articles)

    print("Generating IB report...")
    briefing_generator.create_intelligence_briefing()

    print("Finished successfully.")
    #"""

if __name__ == "__main__":
    main()

import collector.rss_collector as rss_collector
import reporter.report_generator as report_generator

def main():

    print("Starting article collection...")

    articles = rss_collector.collect_articles()

    rss_collector.save_articles(articles)

    report_generator.generate_report(articles)
    

    print("Finished successfully.")


if __name__ == "__main__":
    main()
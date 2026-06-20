from storage.s3_client import S3Storage

cloud = S3Storage()


def upload_daily_articles(date: str):

    cloud.upload_file(
        f"output/articles/{date}.json",
        cloud.article_key(date)
    )


def upload_daily_briefing(date: str):

    cloud.upload_file(
        f"output/briefings/IB_{date}.md",
        cloud.briefing_key(date)
    )
from storage.s3_client import S3Storage

cloud = S3Storage()


def upload_articles(date: str,content):

    cloud.upload_content(
        content,
        cloud.article_key(date)
    )


def upload_briefing(date: str,file_input):

    cloud.upload_content(
        file_input,
        cloud.briefing_key(date)
    )

def download_articles(date: str):

    cloud.download_file(
        f"output/articles/{date}.json",
        cloud.article_key(date)
    )


def download_briefing(date: str):

    cloud.download_file(
        f"output/briefings/IB_{date}.md",
        cloud.briefing_key(date)
    )
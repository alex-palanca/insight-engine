import logging
from datetime import datetime,timezone, timedelta
from pipeline.ingest import ingest
from pipeline.enrich import enrich

logger = logging.getLogger(__name__)

def backfill(
        min_date: str,
        max_date: str
):
    # S3 file will be saved as the min_date
    upload_date_str = min_date
    # Arg conversion to datetime format
    min_date = datetime.fromisoformat(min_date).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    max_date = (datetime.fromisoformat(max_date).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)+ timedelta(days=1))

    if min_date >= max_date:
        raise ValueError("max_date must be the same as or later than min_date.")

    # If applying a range, articles will upload to s3 in a single object
    ingest(upload_date_str,min_date,max_date)
    enrich(upload_date_str)

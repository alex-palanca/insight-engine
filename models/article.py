from pydantic import BaseModel, HttpUrl, Field, field_validator
from datetime import date
import re

# We can move your global constants here
MIN_SUMMARY_LENGTH = 100
INVALID_SUMMARY_MARKERS = [
    "Unknown",
    "no summary available",
    "summary unavailable",
    "unable to retrieve summary",
    "read more",
    "continue reading",
    "click here",
    # common metadata blocks from aggregators (Article/Comments/Points blocks)
    "article url:",
    "comments url:",
    "points:",
    "# comments",
    "source:",
    "url:",
    "Link:",
    # URLs and tracking
    "http://",
    "https://",
    "www.",
    "utm_",
    # social / external hosts
    "youtube.com",
    "vimeo.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "t.co",
    "facebook.com",
    "github.com",
    "news.ycombinator.com",
    # HTML / embed / image markers
    "<img",
    "<iframe",
    "<video",
    "src=",
    "href=",
    "data:image/",
    "&",
    # promotional / commercial noise
    "promo",
    "promo code",
    "coupon",
    "coupon code",
    "discount",
    "% off",
    "deal",
    "sale",
    "sponsored",
    "ad:",
    "buy now",
    "shop",
    "subscribe",
    "sign up",
    "newsletter",
    # media labels / podcast/video boilerplate
    "video",
    "audio",
    "podcast",
    "livestream",
    "gallery",
    "photo",
]

class Article(BaseModel):
    title: str = Field(..., description="Headline of the article")
    link: HttpUrl = Field(..., description="URL of the article")
    published: date = Field(..., description="Exact date of publication")
    source: str
    category: str
    source_tags: list[str] = Field(
        default_factory=list, 
        description="High-trust tags manually assigned in feeds.yaml"
    )
    article_tags: list[str] = Field(
        default_factory=list, 
        description="Variable-trust tags extracted natively from the RSS feed"
    )
    summary: str
    source_url: HttpUrl = Field(..., description="URL of the RSS feed source")


    @field_validator('summary')
    @classmethod
    def clean_and_validate_summary(cls, v: str) -> str:
        # Clean the summary
        cleaned = re.sub(r'<img[^>]*>', '', v, flags=re.IGNORECASE)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        cleaned = cleaned.replace('&nbsp;', ' ').strip()

        # 2. Validate the summary (previously is_valid_summary)
        normalized = cleaned.lower()
        if len(normalized) < MIN_SUMMARY_LENGTH:
            raise ValueError(f"Summary too short ({len(normalized)} chars)")
        
        if any(marker in normalized for marker in INVALID_SUMMARY_MARKERS):
            raise ValueError("Summary contains invalid marker")
        
        return cleaned
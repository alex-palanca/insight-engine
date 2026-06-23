from utils import text_utils as ut

# Invalid summary markers to filter out low-quality content
INVALID_SUMMARY_MARKERS = [
    "Unknown"
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

def is_valid_summary(summary: str, min_length: int = 180) -> bool:
    if not summary:
        return False
    normalized = summary.strip().lower()
    if len(normalized) < min_length:
        return False
    if any(marker in normalized for marker in INVALID_SUMMARY_MARKERS):
        return False

    return True

def clean_batch(raw_articles: list) -> list:

    clean_articles = []

    for article in raw_articles:
        # 1. Clean the HTML out of the summary
        cleaned_text = ut.clean_summary(article.get("summary", "Unknown"))

        # 2. Check if it passes your quality filters
        if is_valid_summary(cleaned_text):
            # Update the article with the clean text and keep it
            article["summary"] = cleaned_text
            clean_articles.append(article)
            
    return clean_articles
        
            


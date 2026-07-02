import re
import unicodedata
import uuid
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

ISOLATE_ID_NAMESPACE = uuid.UUID('02360b9b-c481-4ae9-87c8-06f43b81863e')

def normalize_url(url: str) -> str:
    """Strips tracking parameters to standardize the URL."""
    if not url:
        return ""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    clean_params = {k: v for k, v in query_params.items() if not k.lower().startswith('utm_')}
    clean_query = urlencode(clean_params, doseq=True)
    clean_url = urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.params, clean_query, ''))
    return clean_url.rstrip('/')

def normalize_title(title: str) -> str:
    if not title: return ""
    normalized = unicodedata.normalize('NFKD', title).encode('ASCII', 'ignore').decode('utf-8')
    normalized = re.sub(r'[^\w\s]', '', normalized.lower())
    return re.sub(r'\s+', ' ', normalized).strip()

def generate_article_id(title: str, url: str) -> uuid.UUID:
    safe_url = normalize_url(url)
    safe_title = normalize_title(title)

    composite_string = f"{safe_title}|{safe_url}"
    
    return uuid.uuid5(ISOLATE_ID_NAMESPACE, composite_string)
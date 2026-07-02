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

def generate_article_id(url: str) -> uuid.UUID:
    safe_url = normalize_url(url)
    
    return uuid.uuid5(ISOLATE_ID_NAMESPACE, safe_url)
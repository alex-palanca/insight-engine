import re
import unicodedata
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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

def normalize_text(content: str) -> str:
    if not content: 
        return ""
    normalized = unicodedata.normalize('NFKD', content).encode('ASCII', 'ignore').decode('utf-8')
    normalized = re.sub(r'[^\w\s]', '', normalized.lower())
    return re.sub(r'\s+', ' ', normalized).strip()

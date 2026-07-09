import re
import unicodedata
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

KNOWN_PUBLISHERS = {
    "bbc.co.uk": "BBC",
    "bbc.com": "BBC",
    "reuters.com": "Reuters",
    "apnews.com": "AP News",
    "axios.com": "Axios",
    "techcrunch.com": "TechCrunch",
    "theverge.com": "The Verge",
    "wired.com": "Wired",
    "arstechnica.com": "Ars Technica",
    "cnn.com": "CNN",
    "nytimes.com": "The New York Times",
    "washingtonpost.com": "The Washington Post",
    "forbes.com": "Forbes",
    "bloomberg.com": "Bloomberg",
    "ft.com": "Financial Times",
    "theguardian.com": "The Guardian",
    "aljazeera.com": "Al Jazeera",
    "cnbc.com": "CNBC",
    "theregister.com": "The Register",
    "zdnet.com": "ZDNet",
    "venturebeat.com": "VentureBeat",
    "engadget.com": "Engadget",
}

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

def build_link_label(url: str, source_name: str | None = None) -> str:
    """Create a readable label for a URL such as 'BBC | News'."""
    if not url:
        return "Untitled link"

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().replace("www.", "")

    publisher = source_name or KNOWN_PUBLISHERS.get(host) or host.split(".")[0].title()
    segments = [s for s in parsed.path.strip("/").split("/") if s]
    section = None
    for segment in segments:
        if segment.isdigit() or segment in {"article", "articles", "story", "stories", "video", "videos"}:
            continue
        section = segment.replace("-", " ").replace("_", " ").strip()
        break

    if section and section.lower() not in {"home", "index"}:
        return f"{publisher} | {section.title()}"
    return publisher
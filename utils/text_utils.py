import re

def clean_summary(summary: str) -> str:
    # Remove HTML tags and image references
    cleaned = re.sub(r'<img[^>]*>', '', summary, flags=re.IGNORECASE)
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    cleaned = cleaned.replace('&nbsp;', ' ').strip()
    return cleaned



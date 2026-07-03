import uuid
import utils.text_utils as utils

ISOLATE_ID_NAMESPACE = uuid.UUID('02360b9b-c481-4ae9-87c8-06f43b81863e')

def generate_article_id(title: str, url: str) -> uuid.UUID:
    safe_url = utils.normalize_url(url)
    safe_title = utils.normalize_text(title)

    composite_string = f"{safe_title}|{safe_url}"
    
    return uuid.uuid5(ISOLATE_ID_NAMESPACE, composite_string)
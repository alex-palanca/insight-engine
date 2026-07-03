from pydantic import BaseModel

class EventMetadata(BaseModel):
    title: str
    summary: str
    tags: list[str]
    importance: str
    category: str
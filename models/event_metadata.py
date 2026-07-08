from enum import Enum
from pydantic import BaseModel, Field
from utils.prompt_loader import load_prompt


class EventType(str, Enum):
    announcement = "announcement"
    policy_change = "policy_change"
    conflict = "conflict"
    market_move = "market_move"
    breakthrough = "breakthrough"
    incident = "incident"
    personnel = "personnel"
    other = "other"


class EntityType(str, Enum):
    person = "person"
    organization = "organization"
    country = "country"
    technology = "technology"
    other = "other"


class Entity(BaseModel):
    name: str = Field(description="Lowercase, underscore-separated entity name, e.g. 'united_states'.")
    type: EntityType = Field(description="The kind of entity.")


# ── CREATE ──────────────────────────────────────────────────────────────────
class EventCreate(BaseModel):
    title: str = Field(description="Clear, factual, specific headline naming the key actor(s) and action.")
    summary: str = Field(description="2-4 sentence self-contained factual anchor for the event.")
    event_type: EventType = Field(description="Exactly one value from the fixed event-type taxonomy.")
    entities: list[Entity] = Field(description="3-8 central named entities as typed objects.")
    domains: list[str] = Field(description="One or more domains from the DOMAINS registry.")


# ── UPDATE ──────────────────────────────────────────────────────────────────
class EventUpdate(BaseModel):
    material_change: bool = Field(
        description="True only if the new articles add a genuinely new fact/actor/shift not already in the summary."
    )
    delta_text: str = Field(
        description="One change-shaped sentence describing only the increment. Empty string if material_change is false."
    )
    revised_summary: str = Field(
        description="Existing summary grown by accretion to integrate the new development. Unchanged if material_change is false."
    )


EVENT_CREATE_PROMPT = load_prompt("new_event.txt")
EVENT_UPDATE_PROMPT = load_prompt("update_event.txt")
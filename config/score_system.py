# config/scoring.py
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class ArticleScore(BaseModel):
    article_index: int = Field(
        ge=0,
        description="The index of the article from the batch (e.g., 0, 1, 2) to map it back."
    )
    immediacy: int = Field(ge=0,le=20,description="Score 0-20: Does this affect markets, policy, or operations today/this week?")
    scale: int = Field(ge=0,le=20,description="Score 0-20: How many people, organizations, or markets are directly affected?")
    permanence: int = Field(ge=0,le=20,description="Score 0-20: Is this a one-time event or a structural shift?")
    reverberance: int = Field(ge=0,le=20,description="Score 0-20: Does this trigger cascading secondary effects?")
    novelty: int = Field(ge=0,le=20,description="Score 0-20: Is this new information or a predictable continuation of known trends?")
    
    justification: str = Field(description="A 1-sentence justification for the total score.")
    ai_summary: str = Field(description="A dense, 3-bullet point summary of the core facts.")

    tags: list[str] = Field(
        description=(
            "3-6 lowercase, underscore-separated tags identifying the core "
            "entities and topic of this article (e.g. 'nato', 'ukraine', "
            "'interest_rates'). Prefer specific named entities over generic "
            "category words. Always populate this field."
        )
    )

    @computed_field
    @property
    def total_score(self)->int:
        return sum([self.immediacy,self.scale,self.permanence,self.reverberance,self.novelty])

class BatchEvaluation(BaseModel):
    evaluations: list[ArticleScore] = Field(
        description="A list of evaluations, one for each article provided in the prompt."
    )

class ArticleFilter(BaseModel):
    article_index: int = Field(
        ge=0,
        description="The index of the article from the batch (e.g., 0, 1, 2) to map it back.",
    )

    decision: Literal["keep", "drop"] = Field(
        description=(
            "'keep' if the article deserves further enrichment; "
            "'drop' if the article has no use enriching and keeping"
            "for future analysis is not worth the cost. "
            "When uncertain, choose 'keep'."
        )
    )

    reason: str = Field(
        min_length=1,
        description="One short sentence explaining the filtering decision.",
    )


class BatchFilterEvaluation(BaseModel):
    evaluations: list[ArticleFilter] = Field(
        description="One filtering decision for each article in the input batch."
    )
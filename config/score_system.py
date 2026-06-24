# config/scoring.py
from pydantic import BaseModel, Field

class ArticleScore(BaseModel):
    article_index: int = Field(
        description="The index of the article from the batch (e.g., 0, 1, 2) to map it back."
    )
    immediacy: int = Field(description="Score 0-20: Does this affect markets, policy, or operations today/this week?")
    scale: int = Field(description="Score 0-20: How many people, organizations, or markets are directly affected?")
    permanence: int = Field(description="Score 0-20: Is this a one-time event or a structural shift?")
    reverberance: int = Field(description="Score 0-20: Does this trigger cascading secondary effects?")
    novelty: int = Field(description="Score 0-20: Is this new information or a predictable continuation of known trends?")
    total_score: int = Field(description="The sum of the 5 metrics (0-100).")
    
    justification: str = Field(description="A 1-sentence justification for the total score.")
    ai_summary: str = Field(description="A dense, 3-bullet point summary of the core facts.")

class BatchEvaluation(BaseModel):
    evaluations: list[ArticleScore] = Field(
        description="A list of evaluations, one for each article provided in the prompt."
    )

SCORING_SYSTEM_PROMPT = """
You are a senior intelligence analyst. Evaluate the following batch of articles.
For each article, extract a dense 3-bullet summary and grade it strictly using the 5x20 framework.
Be aggressive with your filtering. Most standard news should score below 50. Only paradigm-shifting events should score above 80.
"""
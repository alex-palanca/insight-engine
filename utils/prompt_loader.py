from pathlib import Path
from functools import lru_cache

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache(maxsize=None)
def load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ directory. Cached after first read."""
    prompt_path = PROMPTS_DIR / filename
    return prompt_path.read_text(encoding="utf-8")
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Ensure we always look for .env in the project root, regardless of where the script runs from
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

# Load variables
load_dotenv(dotenv_path=ENV_PATH)

def get_env_var(name: str, default: Optional[str] = None) -> str | None:
    """Return a secret from Streamlit or environment variable."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError

        if hasattr(st, "secrets"):
            try:
                return st.secrets.get(name, os.getenv(name, default))
            except StreamlitSecretNotFoundError:
                return os.getenv(name, default)
    except ModuleNotFoundError:
        pass

    return os.getenv(name, default)
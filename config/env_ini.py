import os
from pathlib import Path

from dotenv import load_dotenv

# Ensure we always look for .env in the project root, regardless of where the script runs from
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def load_environment(env: str) -> str:
    env = (env or os.getenv("APP_ENV") or "dev").lower()

    if env not in {"dev", "prod"}:
        raise ValueError(f"Unknown APP_ENV: {env}. Use 'dev' or 'prod'.")

    env_file = PROJECT_ROOT / f".env.{env}"
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=False)
        
    os.environ["APP_ENV"] = env
    return env

def get_env_var(name: str) -> str | None:
    """Return a secret from Streamlit or environment variable."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError

        if hasattr(st, "secrets"):
            try:
                return st.secrets.get(name, os.getenv(name))
            except StreamlitSecretNotFoundError:
                return os.getenv(name)
    except ModuleNotFoundError:
        pass

    return os.getenv(name)
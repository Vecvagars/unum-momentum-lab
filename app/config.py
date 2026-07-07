import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_openai_client() -> OpenAI:
    api_key = require_env("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def get_luma_api_key() -> str:
    return require_env("LUMA_API_KEY")

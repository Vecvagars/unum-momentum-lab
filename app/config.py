import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LUMA_API_KEY = os.getenv("LUMA_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(f"OPENAI_API_KEY not found. Checked: {ENV_PATH}")

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# AI provider
USE_AI_PROVIDER = os.getenv("USE_AI_PROVIDER", "openrouter").strip().lower()

# OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat").strip()

# Legacy compatibility
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 🎯 QuickTab Firefox Profile
QUICKTAB_PROFILE = Path.home() / ".quicktab-profile" / "quicktab-weather"
GECKODRIVER_PATH = os.getenv("GECKODRIVER_PATH", "/usr/bin/geckodriver").strip()
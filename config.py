import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 🎯 QuickTab Firefox Profile
QUICKTAB_PROFILE = Path.home() / ".quicktab-profile" / "quicktab-weather"
GECKODRIVER_PATH = os.getenv("GECKODRIVER_PATH", "/usr/bin/geckodriver")


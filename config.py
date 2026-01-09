import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 🎯 QuickTab Firefox Profile
QUICKTAB_PROFILE = Path.home() / ".quicktab-profile" / "quicktab-weather"
GECKODRIVER_PATH = os.getenv("GECKODRIVER_PATH", "/usr/bin/geckodriver")

def ensure_profile():
    """Жёстко используем default-release профиль Firefox"""
    profiles_path = Path.home() / ".mozilla" / "firefox"
    
    # 🔥 ТОЛЬКО default-release
    profile = next(profiles_path.glob("*default-release"), None)
    if profile:
        print(f"🎯 default-release найден: {profile}")
        return str(profile)
    
    # Fallback на любой default*
    default_profile = next(profiles_path.glob("*default*"), None)
    if default_profile:
        quicktab_path = Path.home() / ".quicktab-profile" / "quicktab-weather"
        os.makedirs(quicktab_path.parent, exist_ok=True)
        if not quicktab_path.exists():
            os.symlink(default_profile, quicktab_path)
        print(f"🔗 Симлинк на default: {quicktab_path}")
        return str(quicktab_path)
    
    # Если совсем нет - создаем временный
    temp_profile = Path(tempfile.mkdtemp(prefix="quicktab-firefox-"))
    print(f"🆕 Создан временный профиль: {temp_profile}")
    return str(temp_profile)

# Экспортируем константы для импорта

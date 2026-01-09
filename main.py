from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import time
import re
import os
import tempfile
import signal
import sys
import subprocess
from bs4 import BeautifulSoup
from pathlib import Path

print("🚀 QuickTab: FIREFOX DEFAULT + CHROMIUM | ARCH LINUX")

driver = None
temp_profile = None
browser_name = "Неизвестно"
running = True
firefox_driver = None

def kill_firefox_processes():
    """Принудительно убиваем Firefox процессы"""
    print("🧹 Убиваем Firefox...")
    try:
        subprocess.run(["pkill", "-f", "geckodriver"], capture_output=True)
        subprocess.run(["pkill", "-f", "firefox"], capture_output=True)
        time.sleep(1)
        print("✅ Firefox процессы остановлены")
    except:
        pass

def get_firefox_default_profile():
    profiles_path = Path.home() / ".mozilla" / "firefox"
    
    default = None
    for profile in profiles_path.glob("*default"):
        default_release = profile
        break
    
    if default_release:
        print(f"🎯 НАЙДЕН default: {default}")
        return str(default_release)
    
    # Fallback: любой default*
    for profile in profiles_path.glob("*default*"):
        print(f"🎯 Используем default: {profile}")
        return str(profile)
    
    raise FileNotFoundError("default НЕ НАЙДЕН!")

def safe_driver_check():
    global driver
    if not driver: return False
    try:
        driver.title
        return True
    except: return False

def safe_refresh():
    if not safe_driver_check(): return False
    try:
        driver.refresh()
        time.sleep(3)
        return True
    except: return False

def signal_handler(sig, frame):
    global running
    print("\n🛑 Ctrl+C - остановка...")
    running = False
    sys.exit(0)

def cleanup():
    global driver, temp_profile
    print("\n🔒 Закрытие...")
    if driver:
        try: driver.quit()
        except: pass
    if temp_profile and os.path.exists(temp_profile):
        try:
            import shutil
            shutil.rmtree(temp_profile, ignore_errors=True)
        except: pass

def init_firefox():
    global driver, browser_name, firefox_driver
    
    print("🦊 Запуск Firefox DEFAULT...")
    try:
        firefox_options = FirefoxOptions()
        
        # КРИТИЧЕСКИЕ ОПЦИИ ДЛЯ DEFAULT PROFILE
        firefox_options.add_argument("--disable-web-security")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--disable-dev-shm-usage")
        
        # ОТКЛЮЧАЕМ ВСЕ НАСТРОЙКИ WEBDRIVER ДЛЯ DEFAULT
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        firefox_options.set_preference("marionette.log.level", "FATAL")
        
        # ИСПОЛЬЗУЕМ ТОЛЬКО DEFAULT-RELEASE
        profile_path = get_firefox_default_profile()
        firefox_options.add_argument(f"-profile")
        firefox_options.add_argument(profile_path)
        
        print(f"📁 Профиль: {profile_path}")
        
        # Geckodriver с логами
        firefox_service = FirefoxService()
        firefox_driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
        driver = firefox_driver
        driver.set_page_load_timeout(20)
        
        browser_name = "Firefox DEFAULT"
        print("✅ FIREFOX DEFAULT РАБОТАЕТ!")
        return True
        
    except Exception as e:
        print(f"❌ Firefox DEFAULT ошибка: {e}")
        kill_firefox_processes()
        return False

def init_chromium():
    global driver, temp_profile, browser_name
    print("🔥 Fallback Chromium...")
    try:
        options = Options()
        temp_profile = tempfile.mkdtemp(prefix="quicktab-chrome-")
        options.add_argument(f"--user-data-dir={temp_profile}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-images")
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(20)
        browser_name = "Chromium"
        print("✅ Chromium готов!")
        return True
    except Exception as e:
        print(f"❌ Chromium ошибка: {e}")
        return False

def clean_text(text):
    if not text: return "Не найдено"
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    return re.sub(r'\s+', ' ', soup.get_text()).strip()[:80]

def get_weather_data(driver):
    if not safe_driver_check():
        return {'temp': 'Сессия потеряна', 'desc': '', 'wind': '', 'humidity': ''}
    
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text
        temp_match = re.search(r'([+-]?\s?\d{1,2}[°°])', page_text[:1000])
        temp = clean_text(temp_match.group(1)) if temp_match else "Не найдено"
        
        if temp != "Не найдено" and not re.match(r'^[+-]', temp):
            temp = "+" + temp.strip()
        
        desc_patterns = ['облачно', 'дождь', 'ясно', 'пасмурно', 'снег', 'туман', 'морось', 'прояснения']
        desc = "Не найдено"
        page_lower = page_text.lower()
        for pattern in desc_patterns:
            if pattern in page_lower:
                desc = pattern.capitalize()
                break
        
        page_source = driver.page_source.lower()
        wind_match = re.search(r'ветер[:\s]*.*?(\d+[,\.]\d+|\d+)\s*м/с', page_source)
        wind = clean_text(wind_match.group(1)) + " м/с" if wind_match else 'Не указано'
        
        humidity_match = re.search(r'влажность[:\s]*?(\d+%)', page_source)
        humidity = clean_text(humidity_match.group(1)) if humidity_match else 'Не указано'
        
    except Exception:
        return {
            'temp': 'Ошибка', 'desc': 'Ошибка', 
            'wind': 'Не указано', 'humidity': 'Не указано'
        }
    
    return {
        'temp': temp,
        'desc': desc,
        'wind': wind,
        'humidity': humidity
    }


def print_weather(weather_data):
    print("\n" + "═"*70)
    print(f"🌡️  QUICKTAB | {browser_name} | БЕЛОРЕЧЕНСК")
    print("═"*70)
    print(f"🌡️ Температура:  {weather_data['temp']}")
    print(f"☁️  Условия:      {weather_data['desc']}")
    print(f"💨 Ветер:        {weather_data['wind']}")
    print(f"💧 Влажность:    {weather_data['humidity']}")
    print("═"*70)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

success = init_firefox()
if not success:
    print("🔄 Firefox DEFAULT провалился -> Chromium...")
    kill_firefox_processes()
    success = init_chromium()

if not success:
    print("💥 НИ ОДИН БРАУЗЕР НЕ ЗАПУСТИЛСЯ!")
    sys.exit(1)

wait = WebDriverWait(driver, 10)

try:
    print(f"🌍 Загружаю погоду в {browser_name}...")
    driver.get("https://yandex.ru/pogoda/ru/belorechensk")
    time.sleep(3)

    if safe_driver_check():
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        weather = get_weather_data(driver)
        print_weather(weather)
        
        print("\n✅ QUICKTAB РАБОТАЕТ!")
        print("📍 БЕЛОРЕЧЕНСК")
        print("🛑 Ctrl+C для выхода")
        if temp_profile: print(f"🔒 Временный профиль: {temp_profile}")

        cycle = 1
        while running:
            if not safe_driver_check(): break
            time.sleep(60)
            if not running: break
            print(f"\n🔄 Обновление #{cycle}...")
            if safe_refresh():
                weather = get_weather_data(driver)
                print_weather(weather)
            cycle += 1

except Exception as e:
    print(f"❌ Ошибка: {e}")

finally:
    cleanup()
    print("✅ Готово!")

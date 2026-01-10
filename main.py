from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import os
import tempfile
import signal
import sys
import subprocess
from pathlib import Path
import shutil
import threading
import time as time_module

# Импорты модулей с заглушками
try:
    from weather import get_weather_data, print_weather, safe_driver_check, safe_refresh
    from currency import get_currency_data, print_currency
    from news import get_news_data, print_news
except ImportError as e:
    print(f"⚠️ Модуль не найден: {e}")
    print("🔧 Используем заглушки...")
    
    def safe_driver_check(driver): return True
    def safe_refresh(driver): pass
    
    def get_weather_data(driver): 
        return {"city": "Белореченск", "temp": "+5°C", "condition": "Солнечно"}
    def print_weather(data, browser): 
        print(f"🌤️ {data['city']}: {data['temp']}, {data['condition']}")
    
    def get_currency_data(driver): 
        return {"USD": "92.50", "EUR": "100.20"}
    def print_currency(data, browser): 
        print(f"💱 USD: {data['USD']}₽ | EUR: {data['EUR']}₽")
    
    def get_news_data(driver, topic): 
        return [{"title": f"Новость по теме {topic}", "link": "#"}]
    def print_news(data, browser): 
        print(f"📰 {data[0]['title']}")

try:
    from quicktab import __version__
except ImportError:
    __version__ = "0.2.0"
print(f"🚀 QuickTab v{__version__}")

driver = None
temp_profile = None
browser_name = "Неизвестно"
running = True
firefox_driver = None
request_count = 0  

def browser_monitor():
    """Проверяет браузер каждые 2 сек"""
    global running
    while running:
        if driver and not safe_driver_check(driver):
            print("\n💥 БРАУЗЕР ЗАКРЫТ ПОЛЬЗОВАТЕЛЕМ!")
            running = False
            cleanup()
            sys.exit(0)
        time_module.sleep(2)

def open_new_tab(driver):
    old_count = len(driver.window_handles)
    print(f"\n🔍 Было вкладок: {old_count}")
    
    try:
        # Метод 1: Ctrl+T 
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('t').key_up(Keys.CONTROL).perform()
        time.sleep(1.2)
        
        if len(driver.window_handles) > old_count:
            driver.switch_to.window(driver.window_handles[-1])
            return True
        
        # Метод 2: JavaScript 
        driver.execute_script("window.open('about:blank', '_blank');")
        time.sleep(1.5)
        
        WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > old_count)
        driver.switch_to.window(driver.window_handles[-1])
        return True
        
    except TimeoutException:
        print("❌ Не удалось открыть новую вкладку!")
        return False
    except Exception as e:
        print(f"❌ Ошибка вкладки: {e}")
        return False

def signal_handler(sig, frame):
    global running
    print("\n🛑 Ctrl+C...")
    running = False
    cleanup()
    sys.exit(0)

def cleanup():
    global driver, temp_profile
    print("\n🔒 Закрытие браузера...")
    if driver:
        try:
            driver.quit()
            print("✅ Браузер закрыт")
        except:
            print("⚠️ Ошибка закрытия")
        driver = None
    if temp_profile and os.path.exists(temp_profile):
        shutil.rmtree(temp_profile, ignore_errors=True)
    temp_profile = None

def show_main_menu():
    print("\n" + "═"*70)
    print(" QUICKTAB | Что вы хотите посмотреть?")
    print("═"*70)
    print("1. 🌤️  ПОГОДА")
    print("2. 💱  КУРСЫ")
    print("3. 📰  НОВОСТИ")
    print("═"*70)
    return input("Выберите (1-3): ").strip()

def show_news_menu():
    while True:
        print("\n" + "═"*70)
        print("📰 НОВОСТИ | Выберите тему:")
        print("═"*70)
        print("1. 🛡️ Кибербезопасность")
        print("2. 🌍 Политика")
        print("3. 💰 Экономика") 
        print("4. 🚀 Технологии")
        print("═"*70)
        choice = input("Выберите (1-4): ").strip()
        if choice in ["1", "2", "3", "4"]:
            return choice
        print("❌ Введите 1, 2, 3 или 4")

def get_modules():
    while True:
        choice = show_main_menu()
        if choice == "1": return ["weather"]
        elif choice == "2": return ["currency"]
        elif choice == "3":
            news_choice = show_news_menu()
            news_topics = {"1": "cyber", "2": "politics", "3": "economy", "4": "tech"}
            return [("news", news_topics.get(news_choice, "politics"))]
        else:
            print("❌ Введите 1, 2 или 3")

def kill_firefox_processes():
    print("🧹 Убиваем Firefox...")
    try:
        subprocess.run(["pkill", "-f", "geckodriver"], capture_output=True)
        subprocess.run(["pkill", "-f", "firefox"], capture_output=True)
        time.sleep(1)
        print("✅ Firefox остановлен")
    except: pass

def get_firefox_default_profile():
    profiles_path = Path.home() / ".mozilla" / "firefox"
    for profile in profiles_path.glob("*default*"):
        print(f"🎯 Профиль: {profile}")
        return str(profile)
    raise FileNotFoundError("Firefox default профиль не найден!")

def init_firefox():
    global driver, browser_name, firefox_driver
    print("🦊 Firefox...")
    try:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--disable-web-security")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-gpu")
        
        firefox_options.set_preference("dom.popup_maximum", 20)
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        
        profile_path = get_firefox_default_profile()
        firefox_options.add_argument(f"--profile")
        firefox_options.add_argument(profile_path)
        
        firefox_service = FirefoxService()
        firefox_driver = webdriver.Firefox(service=firefox_service, options=firefox_options)
        driver = firefox_driver
        driver.set_page_load_timeout(25)
        
        print("✅ Firefox готов!")
        browser_name = "Firefox"
        return True
    except Exception as e:
        print(f"❌ Firefox: {e}")
        return False

def init_chromium():
    global driver, temp_profile, browser_name
    print("🔥 Chromium...")
    try:
        options = Options()
        temp_profile = tempfile.mkdtemp(prefix="quicktab-")
        options.add_argument(f"--user-data-dir={temp_profile}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(25)
        print("✅ Chromium готов!")
        browser_name = "Chromium"
        return True
    except Exception as e:
        print(f"❌ Chromium: {e}")
        return False

print("🚀 Запуск браузера...")
success = init_firefox()
if not success:
    kill_firefox_processes()
    success = init_chromium()

if not success:
    print("💥 Браузер не запустился!")
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
monitor_thread = threading.Thread(target=browser_monitor, daemon=True)
monitor_thread.start()

print("✅ QuickTab готов!")

while running:
    request_count += 1  
        
    MODULES = get_modules()
    print(f"✅ Загружаю: {', '.join([m[0] if isinstance(m, tuple) else m for m in MODULES])}")
    
    try:
        for idx, module_info in enumerate(MODULES):
            print(f"\n--- МОДУЛЬ {idx+1}/{len(MODULES)} ---")
            
            if idx > 0 or request_count > 1:
                open_new_tab(driver)
            
            module = module_info[0] if isinstance(module_info, tuple) else module_info
            params = module_info[1] if isinstance(module_info, tuple) else None
            
            print(f"📂 {module} {params or ''}")
            
            if module == "weather":
                driver.get("https://yandex.ru/pogoda/ru/belorechensk")
                time.sleep(4)
                data = get_weather_data(driver)
                print_weather(data, browser_name)
                
            elif module == "currency":
                driver.get("https://www.cbr.ru/currency_base/daily/")
                time.sleep(6)
                data = get_currency_data(driver)
                print_currency(data, browser_name)
                
            elif module == "news":
                print(f"📰 {params}")
                data = get_news_data(driver, params)
                print_news(data, browser_name)
        
        print(f"\n✅ Запрос #{request_count} завершен! Вкладок: {len(driver.window_handles)}")
        print("📍 Enter = НОВЫЙ запрос | Ctrl+C = выход")
        input("⏎ Enter...")
        
    except KeyboardInterrupt:
        print("\n🛑 Выход...")
        break
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        time.sleep(1)
        continue

cleanup()
print("✅ QuickTab завершен!")

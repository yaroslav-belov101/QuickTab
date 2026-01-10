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
import os
import tempfile
import signal
import sys
import subprocess
from pathlib import Path

<<<<<<< HEAD
=======
# Импорты модулей
>>>>>>> d37d2a1 (QuickTab v0.1.0 (добаление курса валют))
from weather import get_weather_data, print_weather, safe_driver_check, safe_refresh
from currency import get_currency_data, print_currency

try:
    from quicktab import __version__
except ImportError:
    __version__ = "0.1.0"
print(f"🚀 QuickTab v{__version__}")

def show_menu():
<<<<<<< HEAD
    print("\n" + "═"*70)
    print(" QUICKTAB | Что вы хотите посмотреть?")
    print("═"*70)
    print("1. 🌤️  ПОГОДА ")
    print("2. 💱  КУРСЫ ВАЛЮТ (ЦБ РФ)")
    print("3. 📊  ВСЕ ВМЕСТЕ")
=======
    """Меню выбора модулей"""
    print("\n" + "═"*70)
    print(" QUICKTAB | Что вы хотите посмотреть?")
    print("═"*70)
    print("1. 🌤️  ПОГОДА")
    print("2. 💱  КУРСЫ ВАЛЮТ (ЦБ РФ)")
    print("3. 📊  ВСЕ ВМЕСТЕ (ОТДЕЛЬНЫЕ ВКЛАДКИ)")
>>>>>>> d37d2a1 (QuickTab v0.1.0 (добаление курса валют))
    print("═"*70)
    return input("Выберите (1-3): ").strip()

choice = show_menu()
if choice == "1":
    MODULES = ["weather"]
elif choice == "2":
    MODULES = ["currency"]
elif choice == "3":
    MODULES = ["weather", "currency"]
else:
    print("❌ Неверный выбор, показываем ВСЁ")
    MODULES = ["weather", "currency"]

print(f"✅ Запуск модулей: {', '.join(MODULES)}")

driver = None
temp_profile = None
browser_name = "Неизвестно"
running = True
firefox_driver = None

def kill_firefox_processes():
    """Убиваем Firefox процессы"""
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
        print(f"🎯 НАЙДЕН default: {default_release}")
        return str(default_release)
    
    for profile in profiles_path.glob("*default*"):
        print(f"🎯 Используем default: {profile}")
        return str(profile)
    
    raise FileNotFoundError("default НЕ НАЙДЕН!")

def signal_handler(sig, frame):
    global running
    print("\n🛑 Ctrl+C - остановка...")
    running = False
    sys.exit(0)

def cleanup():
    global driver, temp_profile
    print("\n🔒 Закрытие...")
    if driver:
        try: 
            driver.quit()
        except: 
            pass
    if temp_profile and os.path.exists(temp_profile):
        try:
            import shutil
            shutil.rmtree(temp_profile, ignore_errors=True)
        except: 
            pass

def init_firefox():
    global driver, browser_name, firefox_driver
    
    print("🦊 Запуск Firefox DEFAULT...")
    try:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--disable-web-security")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--disable-dev-shm-usage")
        
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        firefox_options.set_preference("marionette.log.level", "FATAL")
        
        profile_path = get_firefox_default_profile()
        firefox_options.add_argument(f"-profile")
        firefox_options.add_argument(profile_path)
        print(f"📁 Профиль: {profile_path}")
        
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
    print(f"🌍 Загружаю данные в {browser_name}...")
    
    if safe_driver_check(driver):
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
<<<<<<< HEAD
        tabs = {}  # Словарь вкладок: {index: module}
=======
        tabs = {}  # {tab_index: module}
>>>>>>> d37d2a1 (QuickTab v0.1.0 (добаление курса валют))
        
        # ОТКРЫВАЕМ ВСЕ модули в НОВЫХ вкладках
        for i, module in enumerate(MODULES):
            if i > 0:  # Первая вкладка уже открыта
                driver.execute_script("window.open('');")
<<<<<<< HEAD
                tab_handle = driver.window_handles[i]
                driver.switch_to.window(tab_handle)
=======
                driver.switch_to.window(driver.window_handles[-1])
>>>>>>> d37d2a1 (QuickTab v0.1.0 (добаление курса валют))
            
            if module == "weather":
                driver.get("https://yandex.ru/pogoda/ru/belorechensk")
                time.sleep(3)
                data = get_weather_data(driver)
                print_weather(data, browser_name)
<<<<<<< HEAD
                tabs[i] = module
            elif module == "currency":
                driver.get("https://www.cbr.ru/currency_base/daily/")
                time.sleep(3)
                data = get_currency_data(driver)
                print_currency(data, browser_name)
                tabs[i] = module
        
        print("\n✅ QUICKTAB РАБОТАЕТ!")
        print("📍 Ctrl+C для выхода")
        if temp_profile: 
            print(f"🔒 Временный профиль: {temp_profile}")
        print(f"🆕 Открыто вкладок: {len(tabs)}")
=======
                tabs[len(driver.window_handles)-1] = module
            elif module == "currency":
                driver.get("https://www.cbr.ru/currency_base/daily/")
                time.sleep(5)
                data = get_currency_data(driver)
                print_currency(data, browser_name)
                tabs[len(driver.window_handles)-1] = module
        
        print("\n✅ QUICKTAB РАБОТАЕТ!")
        print(f"🆕 Открыто вкладок: {len(tabs)}")
        print("📍 Ctrl+C для выхода")
        if temp_profile: 
            print(f"🔒 Временный профиль: {temp_profile}")
>>>>>>> d37d2a1 (QuickTab v0.1.0 (добаление курса валют))

        cycle = 1
        while running:
            if not safe_driver_check(driver): 
                break
            time.sleep(60)
            print(f"\n🔄 Обновление #{cycle}...")
            
            # ЦИКЛ по ВСЕМ вкладкам
<<<<<<< HEAD
            for tab_index, module in tabs.items():
                try:
                    driver.switch_to.window(driver.window_handles[tab_index])
                    
                    if safe_refresh(driver):
                        if module == "weather":
                            data = get_weather_data(driver)
                            print_weather(data, browser_name)
                        elif module == "currency":
                            data = get_currency_data(driver)
                            print_currency(data, browser_name)
                except:
                    print(f"⚠️  Ошибка вкладки {tab_index}")
=======
            window_handles = driver.window_handles
            for tab_index, module in tabs.items():
                try:
                    if tab_index < len(window_handles):
                        driver.switch_to.window(window_handles[tab_index])
                        
                        if safe_refresh(driver):
                            if module == "weather":
                                data = get_weather_data(driver)
                                print_weather(data, browser_name)
                            elif module == "currency":
                                data = get_currency_data(driver)
                                print_currency(data, browser_name)
                except Exception as e:
                    print(f"⚠️ Ошибка вкладки {tab_index}: {e}")
>>>>>>> d37d2a1 (QuickTab v0.1.0 (добаление курса валют))
                    continue
                    
            cycle += 1

except Exception as e:
    print(f"❌ Ошибка: {e}")

finally:
    cleanup()
    print("✅ Готово!")


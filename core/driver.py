"""
Оптимизированный WebDriver для скорости
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os
import shutil


class DriverManager:
    """Управление Selenium WebDriver — оптимизированная версия"""
    
    def __init__(self):
        self.driver = None
    
    def init_driver(self, headless: bool = True):
        """Инициализация с настройками для скорости"""
        try:
            options = Options()
            
            if headless:
                options.add_argument("--headless=new")  # Новый быстрый headless
            
            # ⚡ Оптимизации скорости
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Не загружаем картинки
            options.add_argument("--disable-javascript")  # Можно включить если нужен JS
            options.add_argument("--blink-settings=imagesEnabled=false")
            options.add_argument("--disk-cache-size=0")  # Отключаем дисковый кэш
            
            # Анти-детекция
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent
            options.add_argument(
                "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Размер окна (даже в headless)
            options.add_argument("--window-size=1280,720")
            
            # Ищем или скачиваем chromedriver
            chromedriver_path = self._find_chromedriver()
            
            if chromedriver_path:
                service = Service(chromedriver_path)
            else:
                # Очищаем кэш для свежей версии
                wdm_cache = os.path.expanduser("~/.wdm")
                if os.path.exists(wdm_cache):
                    shutil.rmtree(wdm_cache, ignore_errors=True)
                
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # ⚡ Устанавливаем таймауты
            self.driver.set_page_load_timeout(15)  # Макс 15 сек на загрузку страницы
            self.driver.implicitly_wait(2)  # Не ждем элементы долго
            
            print("✅ WebDriver инициализирован (оптимизированный)")
            return self.driver
            
        except Exception as e:
            print(f"❌ Ошибка инициализации WebDriver: {e}")
            return None
    
    def _find_chromedriver(self) -> str:
        """Ищет chromedriver"""
        import shutil
        
        paths = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "/usr/lib/chromium-browser/chromedriver",
            shutil.which("chromedriver"),
        ]
        
        for path in paths:
            if path and os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ WebDriver закрыт")
            except:
                pass
            finally:
                self.driver = None
    
    def is_active(self) -> bool:
        return self.driver is not None
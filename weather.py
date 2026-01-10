from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import time
import re
from bs4 import BeautifulSoup

def clean_text(text):
    """Очищает текст от HTML и лишних пробелов"""
    if not text: 
        return "Не найдено"
    soup = BeautifulSoup(text, 'html.parser')
    return re.sub(r'\s+', ' ', soup.get_text()).strip()[:80]

def safe_driver_check(driver):
    """Проверяет, жив ли драйвер"""
    if not driver: 
        return False
    try:
        driver.title
        return True
    except: 
        return False

def safe_refresh(driver):
    """Безопасно обновляет страницу"""
    if not safe_driver_check(driver): 
        return False
    try:
        driver.refresh()
        time.sleep(3)
        return True
    except: 
        return False


def get_weather_data(driver):
    """Извлекает данные о погоде из страницы"""
    if not safe_driver_check(driver):
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


def print_weather(weather_data, browser_name):
    """Выводит погоду в красивом формате"""
    print("\n" + "═"*70)
    print(f"🌡️  QUICKTAB | {browser_name} | ПОГОДА")
    print("═"*70)
    print(f"🌡️ Температура:  {weather_data['temp']}")
    print(f"☁️  Условия:      {weather_data['desc']}")
    print(f"💨 Ветер:        {weather_data['wind']}")
    print(f"💧 Влажность:    {weather_data['humidity']}")
    print("═"*70)

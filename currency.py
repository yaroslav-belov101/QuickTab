from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import time
import re
from bs4 import BeautifulSoup

def clean_text(text):
    if not text: 
        return "Не найдено"
    soup = BeautifulSoup(text, 'html.parser')
    return re.sub(r'\s+', ' ', soup.get_text()).strip()[:80]

def safe_driver_check(driver):
    if not driver: 
        return False
    try:
        driver.title
        return True
    except: 
        return False

def safe_refresh(driver):
    if not safe_driver_check(driver):
        return False
    try:
        driver.refresh()
        time.sleep(3)
        return True
    except:
        return False

def get_currency_data(driver):
    if not safe_driver_check(driver):
        return {'usd': 'Сессия потеряна', 'eur': 'Сессия потеряна'}
    
    usd = eur = "Не найдено"
    
    try:
        time.sleep(5)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        table = driver.find_element(By.CSS_SELECTOR, "table.data")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        for i, row in enumerate(rows[1:]):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 5: 
                    code = cells[0].text.strip()  
                    name = cells[1].text.strip()  
                    nominal = cells[2].text.strip()  
                    rate = cells[4].text.strip() 
                    
                    # USD = код 840
                    if code == "840":
                        usd = f"{rate} ₽"
                        
                    # EUR = код 978  
                    elif code == "978":
                        eur = f"{rate} ₽"
                        
                    
                    if usd != "Не найдено" and eur != "Не найдено":
                        break       
            except:
                continue
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {'usd': 'Ошибка', 'eur': 'Ошибка'}
    
    return {'usd': usd, 'eur': eur}

def print_currency(currency_data, browser_name):
    print("\n" + "═"*70)
    print(f"💱 QUICKTAB | {browser_name} | КУРСЫ ЦБ РФ")
    print("═"*70)
    print(f"💵 USD: {currency_data['usd']}")
    print(f"💶 EUR: {currency_data['eur']}")
    print("═"*70)

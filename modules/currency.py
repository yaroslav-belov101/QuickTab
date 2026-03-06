"""
Модуль валют — ускоренный парсинг ЦБ РФ с Selenium
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict
import time


# URL курсов ЦБ РФ
CBR_URL = "https://www.cbr.ru/currency_base/daily/"

# URL для BTC/USD
BTC_URL = "https://www.rbc.ru/crypto/currency/btcusd"

# Кэш курсов (обновляется раз в час)
_cache = {
    "usd": None,
    "eur": None,
    "btc": None,
    "timestamp": 0
}
CACHE_TTL = 3600  # 1 час


def _safe_driver_check(driver) -> bool:
    """Быстрая проверка драйвера"""
    if not driver:
        return False
    try:
        driver.title
        return True
    except:
        return False


def _parse_rates_fast(driver) -> Dict[str, str]:
    """Быстрый парсинг курсов из таблицы"""
    usd = eur = "Не найдено"
    
    # Ищем все строки таблицы сразу
    rows = driver.find_elements(By.CSS_SELECTOR, "table.data tr")
    
    for row in rows[1:]:  # Пропускаем заголовок
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 5:
                code = cells[0].text.strip()
                rate = cells[4].text.strip().replace(',', '.')
                
                if code == "840" and usd == "Не найдено":
                    usd = f"{rate} ₽"
                elif code == "978" and eur == "Не найдено":
                    eur = f"{rate} ₽"
                
                if usd != "Не найдено" and eur != "Не найдено":
                    break
        except:
            continue
    
    return {"USD": usd, "EUR": eur}


def _parse_btc_price(driver) -> str:
    """Парсинг цены BTC/USD с RBC"""
    try:
        driver.get(BTC_URL)
        wait = WebDriverWait(driver, 8)
        # Селекторы для RBC
        selectors = [
            ".chart__info-sum",
            ".crypto-chart__price",
            ".currency-chart__value",
            ".js-currency-value",
            ".price-value"
        ]
        
        for selector in selectors:
            try:
                price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                price_text = price_element.text.strip()
                if any(c.isdigit() for c in price_text):
                    # Извлекаем только цифры и точки
                    clean_price = ''.join(c for c in price_text if c.isdigit() or c == '.' or c == ',')
                    if clean_price:
                        return clean_price
            except:
                continue
        
        # Fallback: найти элемент с USD
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'USD') or contains(text(), '$')]")
        for elem in elements[:10]:
            text = elem.text.strip()
            # Ищем текст с USD или $
            if 'USD' in text or '$' in text:
                # Извлекаем цифры
                clean_price = ''.join(c for c in text if c.isdigit() or c == '.' or c == ',')
                if len(clean_price) > 3:
                    return clean_price
        
        return "Не найдено"
    except Exception as e:
        print(f"Ошибка парсинга BTC: {e}")
        return "Не найдено"


def get_currency_data(driver) -> Dict[str, str]:
    """
    Ускоренное получение курсов валют.
    Использует кэширование и явные ожидания.
    """
    global _cache
    
    # Проверяем кэш
    current_time = time.time()
    if _cache["usd"] and _cache["eur"] and _cache["btc"] and (current_time - _cache["timestamp"]) < CACHE_TTL:
        print("💱 [Currency] Использую кэшированные курсы")
        return {"USD": _cache["usd"], "EUR": _cache["eur"], "BTC": _cache["btc"]}
    
    if not _safe_driver_check(driver):
        print("💱 [Currency] Драйвер недоступен, использую заглушку")
        return {"USD": "92.50 ₽", "EUR": "100.20 ₽", "BTC": "95000 USD"}
    
    try:
        print(f"💱 [Currency] Загрузка курсов ЦБ...")
        
        # Загружаем страницу ЦБ
        driver.get(CBR_URL)
        
        # Быстрое ожидание таблицы (макс 8 сек)
        wait = WebDriverWait(driver, 8)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.data")))
        
        # Парсим фиат валюты
        result = _parse_rates_fast(driver)
        
        # Парсим BTC
        btc_price = _parse_btc_price(driver)
        result["BTC"] = btc_price
        
        # Сохраняем в кэш
        if result["USD"] != "Не найдено" and result["EUR"] != "Не найдено" and result["BTC"] != "Не найдено":
            _cache["usd"] = result["USD"]
            _cache["eur"] = result["EUR"]
            _cache["btc"] = result["BTC"]
            _cache["timestamp"] = current_time
            print(f"   ✅ Курсы обновлены: {result['USD']}, {result['EUR']}, {result['BTC']}")
        else:
            print(f"   ⚠️ Не все курсы найдены: {result}")
        
        return result
        
    except TimeoutException:
        print("   ⚠️ Таймаут загрузки ЦБ")
        return {"USD": "Таймаут", "EUR": "Таймаут", "BTC": "Таймаут"}
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return {"USD": "Ошибка", "EUR": "Ошибка", "BTC": "Ошибка"}


def format_currency_for_display(data: Dict[str, str]) -> str:
    """Форматирует курсы для GUI"""
    lines = ["💱 КУРСЫ ВАЛЮТ (ЦБ РФ)"]
    for currency, rate in data.items():
        lines.append(f"{currency}: {rate}")
    return "\n".join(lines) + "\n\n"


def print_currency(currency_data: Dict[str, str], browser_name: str = "Chrome"):
    """Вывод в консоль"""
    print("\n" + "═" * 70)
    print(f"💱 QUICKTAB | {browser_name} | КУРСЫ ЦБ РФ + BTC")
    print("═" * 70)
    print(f"💵 USD: {currency_data['USD']}")
    print(f"💶 EUR: {currency_data['EUR']}")
    print(f"₿ BTC: {currency_data['BTC']}")
    print("═" * 70)


def clear_cache():
    """Очистить кэш курсов (для принудительного обновления)"""
    global _cache
    _cache = {"usd": None, "eur": None, "btc": None, "timestamp": 0}
"""
Модуль валют — ускоренный парсинг ЦБ РФ с Selenium
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict
import time
from .driver_lock import lock as _driver_lock


# URL курсов ЦБ РФ
CBR_URL = "https://cbr.ru/currency_base/daily/"

# URL для BTC/USD
BTC_URL = "https://coinmarketcap.com/currencies/bitcoin/"

# Кэш курсов (обновляется раз в час)
_cache = {
    "USD": None,
    "EUR": None,
    "BTC": None,
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
    usd = eur = "Нет данных"
    
    try:
        # Ищем таблицу с курсами
        table_selectors = ["table.data", "table", ".table", "#content table"]
        table = None
        for sel in table_selectors:
            try:
                table = driver.find_element(By.CSS_SELECTOR, sel)
                print(f"   Найдена таблица с селектором '{sel}'")
                break
            except:
                continue
        
        if not table:
            print("   ❌ Таблица не найдена")
            return {"USD": usd, "EUR": eur}
        
        # Ищем все строки таблицы
        rows = table.find_elements(By.TAG_NAME, "tr")
        print(f"   Найдено строк в таблице: {len(rows)}")
        
        for i, row in enumerate(rows[1:], 1):  # Пропускаем заголовок
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 5:
                    code = cells[0].text.strip()
                    rate = cells[4].text.strip().replace(',', '.')
                    print(f"     Строка {i}: code={code}, rate={rate}")
                    
                    if code == "840" and usd == "Нет данных":  # USD
                        usd = f"{rate} ₽"
                        print(f"       ✅ USD найден: {usd}")
                    elif code == "978" and eur == "Нет данных":  # EUR
                        eur = f"{rate} ₽"
                        print(f"       ✅ EUR найден: {eur}")
                    
                    if usd != "Нет данных" and eur != "Нет данных":
                        print("       ✅ Все валюты найдены")
                        break
            except Exception as e:
                print(f"     Ошибка в строке {i}: {e}")
                continue
        
        # Если не найдено, пробуем поиск по тексту
        if usd == "Нет данных":
            try:
                usd_elements = driver.find_elements(By.XPATH, "//td[contains(text(), 'USD') or contains(text(), '840')]/following-sibling::td[4]")
                if usd_elements:
                    rate = usd_elements[0].text.strip().replace(',', '.')
                    usd = f"{rate} ₽"
                    print(f"   ✅ USD найден по тексту: {usd}")
            except:
                pass
        
        if eur == "Нет данных":
            try:
                eur_elements = driver.find_elements(By.XPATH, "//td[contains(text(), 'EUR') or contains(text(), '978')]/following-sibling::td[4]")
                if eur_elements:
                    rate = eur_elements[0].text.strip().replace(',', '.')
                    eur = f"{rate} ₽"
                    print(f"   ✅ EUR найден по тексту: {eur}")
            except:
                pass
        
        if usd == "Нет данных" or eur == "Нет данных":
            print(f"   ⚠️ Не все валюты найдены: USD={usd}, EUR={eur}")
        
    except Exception as e:
        print(f"   ❌ Ошибка парсинга таблицы: {e}")
    
    return {"USD": usd, "EUR": eur}


def _parse_btc_price(driver) -> str:
    """Парсинг цены BTC/USD с CoinMarketCap"""
    try:
        print(f"   Загрузка BTC с {BTC_URL}")
        driver.get(BTC_URL)
        print("   Страница BTC загружена")
        wait = WebDriverWait(driver, 15)
        # Селекторы для CoinMarketCap
        selectors = [
            ".priceValue span",
            ".sc-65e7f566-0",
            "[data-test='text-cdp-price-display']",
            ".price"
        ]
        
        for selector in selectors:
            try:
                print(f"   Пробую селектор BTC: {selector}")
                price_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                price_text = price_element.text.strip()
                print(f"   Найден текст: {price_text}")
                if any(c.isdigit() for c in price_text):
                    # Извлекаем только цифры и точки
                    clean_price = ''.join(c for c in price_text if c.isdigit() or c == '.' or c == ',')
                    if clean_price:
                        print(f"   BTC цена: {clean_price}")
                        return f"{clean_price} USD"
            except Exception as e:
                print(f"   Селектор {selector} не найден: {e}")
                continue
        
        # Fallback: найти любой элемент с большой ценой
        print("   Поиск любой цены BTC")
        elements = driver.find_elements(By.XPATH, "//*[string-length(text()) > 5 and contains(text(), '.') and number(substring-before(text(), '.')) > 1000]")
        for elem in elements[:5]:
            text = elem.text.strip()
            print(f"   Элемент с ценой: {text}")
            clean_price = ''.join(c for c in text if c.isdigit() or c == '.' or c == ',')
            if len(clean_price) > 4:
                print(f"   BTC цена найдена: {clean_price}")
                return f"{clean_price} USD"
        
        return "Нет данных"
    except Exception as e:
        print(f"Ошибка парсинга BTC: {e}")
        return "Нет данных"


def get_currency_data(driver) -> Dict[str, str]:
    """
    Ускоренное получение курсов валют.
    Использует кэширование и явные ожидания.
    """
    global _cache
    
    # Проверяем кэш
    current_time = time.time()
    if (_cache["USD"] and _cache["EUR"] and _cache["BTC"] and 
        (current_time - _cache["timestamp"]) < CACHE_TTL):
        print("💱 [Currency] Использую кэшированные курсы")
        return {"USD": _cache["USD"], "EUR": _cache["EUR"], "BTC": _cache["BTC"]}
    
    if not _safe_driver_check(driver):
        print("💱 [Currency] Драйвер недоступен, использую заглушку")
        return {"USD": "92.50 ₽", "EUR": "100.20 ₽", "BTC": "95000 USD"}
    
    # Блокируем доступ к драйверу
    with _driver_lock:
        try:
            print(f"💱 [Currency] Загрузка курсов ЦБ...")
            
            # Загружаем страницу ЦБ
            driver.get(CBR_URL)
            print(f"   Страница загружена: {driver.current_url}, title={driver.title}")
            
            # Ждем загрузки страницы и таблицы
            time.sleep(3)
            
            # Скроллим страницу для загрузки динамического контента
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            # Быстрое ожидание таблицы (макс 25 сек)
            wait = WebDriverWait(driver, 25)
            
            # Пробуем разные селекторы для таблицы
            table_selectors = [
                "table.data",
                "table[class='data']",
                ".data",
                "table",
                "[class*='data']",
                "tbody tr:nth-child(2) td:first-child",  # Проверяем наличие данных
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    print(f"   Пробую селектор: {selector}")
                    table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"   ✅ Найдена таблица с селектором: {selector}")
                    break
                except Exception as e:
                    print(f"   ❌ Селектор {selector} не найден: {str(e)[:50]}")
                    continue
            
            # повторный проход при неудаче
            if not table:
                print("   ⚠️ Таблица не найдена, перезагружаем страницу и пробуем снова")
                driver.get(CBR_URL)
                time.sleep(5)
                for selector in table_selectors:
                    try:
                        print(f"   Второй проход: пробую селектор: {selector}")
                        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        print(f"   ✅ Найдена таблица с селектором: {selector} (повтор)")
                        break
                    except Exception as e:
                        print(f"   ❌ Селектор {selector} не найден (повтор): {str(e)[:50]}")
                        continue
            
            if not table:
                print("   ❌ Таблица не найдена ни одним селектором, пробуем анализ source")
                html = driver.page_source
                print(f"   📝 source (начало): {html[:400].replace('\n',' ')}")
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, "html.parser")
                    tbl = soup.find("table")
                    if tbl:
                        print("   🔍 Найдена таблица через BeautifulSoup, разбираю вручную")
                        usd = eur = "Не найдено"
                        for row in tbl.find_all("tr")[1:]:
                            cells = row.find_all("td")
                            if len(cells) >= 5:
                                code = cells[0].text.strip()
                                rate = cells[4].text.strip().replace(',', '.')
                                if code == "840" and usd == "Не найдено":
                                    usd = f"{rate} ₽"
                                    print(f"       ✅ USD найден: {usd}")
                                elif code == "978" and eur == "Не найдено":
                                    eur = f"{rate} ₽"
                                    print(f"       ✅ EUR найден: {eur}")
                                if usd != "Не найдено" and eur != "Не найдено":
                                    break
                        result = {"USD": usd, "EUR": eur}
                    else:
                        print("   🔍 BeautifulSoup тоже не нашёл таблицу")
                        raise TimeoutException("Таблица не найдена")
                except Exception as bs_err:
                    print(f"   ❌ Ошибка при разборе source: {bs_err}")
                    raise TimeoutException("Таблица не найдена")
            else:
                # Парсим фиат валюты
                result = _parse_rates_fast(driver)
            
            # Парсим BTC
            btc_price = _parse_btc_price(driver)
            result["BTC"] = btc_price
        
            # Сохраняем в кэш только если данные валидны
            if (result["USD"] != "Нет данных" and 
                result["EUR"] != "Нет данных" and 
                result["BTC"] != "Нет данных"):
                _cache["USD"] = result["USD"]
                _cache["EUR"] = result["EUR"]
                _cache["BTC"] = result["BTC"]
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
    _cache = {"USD": None, "EUR": None, "BTC": None, "timestamp": 0}
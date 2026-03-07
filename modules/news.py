"""
Модуль новостей — ускоренный парсинг с Selenium
Использует явные ожидания вместо time.sleep
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict, Optional
import time
from .driver_lock import lock as _driver_lock


# Кэш новостей
_news_cache = {
    "cyber": [],
    "politics": [],
    "economy": [],
    "tech": [],
    "timestamp": 0
}
CACHE_TTL = 300  # 5 минут


# Конфигурация источников новостей
NEWS_SITES = {
    "cyber": {
        "url": "https://habr.com/ru/hubs/infosecurity/news/",
        "name": "🛡️ Кибербезопасность",
        "wait_selector": ".tm-articles-list__item",  # Ждем появления статей
        "title_selectors": [
            ".tm-title__link",
            ".tm-articles-list__title-link",
            "article h2 a"
        ],
        "timeout": 8
    },
    "politics": {
        "url": "https://ria.ru/politics/",
        "name": "🌍 Политика",
        "wait_selector": ".list-item",
        "title_selectors": [
            ".list-item__title",
            ".list-item__content-title",
            "[data-test='news-item'] h3"
        ],
        "timeout": 8
    },
    "economy": {
        "url": "https://ria.ru/economy/",
        "name": "💰 Экономика",
        "wait_selector": ".list-item",
        "title_selectors": [
            ".list-item__title",
            ".list-item__content-title"
        ],
        "timeout": 8
    },
    "tech": {
        "url": "https://habr.com/ru/news/",
        "name": "🚀 Технологии",
        "wait_selector": ".tm-articles-list__item",
        "title_selectors": [
            ".tm-title__link",
            ".tm-articles-list__title-link"
        ],
        "timeout": 20
    }
}


def _safe_driver_check(driver) -> bool:
    """Быстрая проверка драйвера"""
    if not driver:
        return False
    try:
        driver.title
        return True
    except Exception:
        return False


def _fast_parse_titles(driver, selectors: List[str], max_items: int = 5) -> List[Dict[str, str]]:
    """Быстрый парсинг заголовков без лишних проверок"""
    results = []
    
    for selector in selectors:
        try:
            # Ищем элементы без ожидания — уже ждали загрузки страницы
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            for elem in elements[:max_items]:
                try:
                    title = elem.text.strip()
                    href = elem.get_attribute("href")
                    
                    if title and len(title) > 5:  # Упрощенная проверка
                        results.append({
                            "title": title[:120],
                            "summary": "",
                            "url": href or ""
                        })
                        
                        if len(results) >= max_items:
                            return results
                            
                except Exception:
                    continue
                    
        except Exception:
            continue
            
        # Если нашли достаточно новостей, выходим
        if len(results) >= max_items:
            break
    
    return results


def get_news_data(driver, topic: str = "cyber") -> List[Dict[str, str]]:
    """
    Ускоренное получение новостей.
    Использует явные ожидания вместо фиксированных задержек.
    """
    # Проверяем кэш
    current_time = time.time()
    if (_news_cache[topic] and 
        (current_time - _news_cache["timestamp"]) < CACHE_TTL):
        print(f"🔍 [News] {NEWS_SITES[topic]['name']} — из кэша ({len(_news_cache[topic])} новостей)")
        return _news_cache[topic]
    
    if not _safe_driver_check(driver):
        return [{"title": "Сессия потеряна", "summary": "WebDriver не отвечает"}]
    
    # Блокируем доступ к драйверу
    with _driver_lock:
        config = NEWS_SITES.get(topic, NEWS_SITES["economy"])
        
        try:
            print(f"🔍 [News] {config['name']} — загрузка...")
            
            # Загружаем страницу
            driver.get(config["url"])
            
            # Быстрое ожидание ключевого элемента (макс timeout секунд)
            wait = WebDriverWait(driver, config["timeout"])
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, config["wait_selector"])
            ))
            
            # Дополнительная микро-задержка для стабильности (опционально)
            # time.sleep(0.5)  # Раскомментировать если нужна стабильность
            
            # Быстрый парсинг
            news_items = _fast_parse_titles(driver, config["title_selectors"], max_items=5)
            
            if not news_items:
                # Fallback: любые ссылки
                links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
                for link in links[:15]:
                    try:
                        title = link.text.strip()
                        href = link.get_attribute("href")
                        if title and 20 < len(title) < 100 and href and 'http' in href:
                            news_items.append({
                                "title": title[:120],
                            "summary": "",
                            "url": href
                        })
                        if len(news_items) >= 3:
                            break
                    except:
                        continue
            
            # Сохраняем в кэш
            _news_cache[topic] = news_items
            _news_cache["timestamp"] = current_time
            
            print(f"   ✅ Найдено: {len(news_items)} новостей")
            return news_items if news_items else [{"title": "Новости не найдены", "summary": ""}]
            
        except TimeoutException:
            print(f"   ⚠️ Таймаут загрузки")
            return [{"title": "Таймаут загрузки", "summary": "Страница загружается слишком долго"}]
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return [{"title": "Ошибка загрузки", "summary": str(e)[:50]}]


def format_news_for_display(news_items: List[Dict[str, str]], topic_name: str) -> str:
    """Форматирует новости для GUI"""
    lines = [f"📰 НОВОСТИ: {topic_name}", "=" * 50, ""]
    
    for i, item in enumerate(news_items, 1):
        title = item.get('title', 'Без названия')
        lines.append(f"{i}. {title}")
        lines.append("")
    
    return "\n".join(lines)


def print_news(news_data: Dict, browser_name: str = "Chrome"):
    """Вывод в консоль (для отладки)"""
    items = news_data.get('news_items', []) if isinstance(news_data, dict) else news_data
    topic = news_data.get('topic', 'Новости') if isinstance(news_data, dict) else 'Новости'
    
    print("\n" + "═" * 70)
    print(f"📰 QUICKTAB | {browser_name} | {topic}")
    print("═" * 70)
    
    for i, item in enumerate(items[:5], 1):
        if isinstance(item, dict):
            title = item.get('title', '')
            url = item.get('url', item.get('summary', ''))
        else:
            title, url = item[0], item[1]
        
        print(f"{i}. {title[:60]}")
        if url and len(str(url)) > 10:
            short = str(url).replace('https://', '')[:40]
            print(f"   {short}...")
    
    print("═" * 70)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import time

def safe_driver_check(driver):
    if not driver: 
        return False
    try:
        driver.title
        return True
    except: 
        return False

NEWS_SITES = {
    "cyber": {
        "url": "https://habr.com/ru/hubs/infosecurity/news/",  
        "name": "🛡️ Кибербезопасность",
        "selectors": [".tm-articles-list__title-link", ".posts__title-link", "article h2 a"]
    },
    "politics": {
        "url": "https://ria.ru/politics/",  
        "name": "🌍 Политика",
        "selectors": [".list-item__title", ".article-item__title", "[data-test='news-item'] h3"]
    },
    "economy": {
        "url": "https://ria.ru/economy/",  
        "name": "💰 Экономика", 
        "selectors": [
            ".list-item__title", 
            ".article-item__title",
            "[data-test='news-item'] h3",
            "h3 a"
        ]
    },
    "tech": {
        "url": "https://habr.com/ru/all/",  
        "name": "🚀 Технологии", 
        "selectors": [".tm-articles-list__title-link", ".posts__title-link"]
    }
}

def get_news_data(driver, topic="politics"):
    """📰 САМ открывает сайт + парсит"""
    if not safe_driver_check(driver):
        print("❌ Драйвер недоступен")
        return {'topic': topic, 'news_items': [('Сессия потеряна', '')]}
    
    site_config = NEWS_SITES.get(topic, NEWS_SITES["economy"])
    news_items = []
    
    print(f"🔍 ОТКРЫВАЮ: {site_config['url']}")
    driver.get(site_config['url'])  
    time.sleep(6)  
    
    print(f"📍 Загружено: {driver.current_url}")
    print(f"🔍 НАЧИНАЮ ПАРСИНГ {site_config['name']}")
    
    try:
        selectors = [
            ".list-item__title", "h3 a", "h2 a", 
            ".article-item__title", ".news-title a"
        ]
        
        for selector in selectors:
            items = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"   '{selector}': {len(items)}")
            
            for item in items[:6]:
                title = item.text.strip()
                href = item.get_attribute("href")
                
                if title and len(title) > 15 and href and href.startswith('http'):
                    news_items.append((title[:120], href))
                    print(f"     ✅ '{title[:50]}...'")
                    if len(news_items) >= 4:
                        break
            
            if len(news_items) >= 3:
                break
        
        if len(news_items) < 2:
            print("🔄 Fallback: любые ссылки...")
            links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
            for link in links[:20]:
                title = link.text.strip()
                href = link.get_attribute("href")
                if (title and 20 < len(title) < 100 and href and 'ria.ru' in href):
                    news_items.append((title, href))
                    print(f"     F: '{title[:40]}...'")
                    if len(news_items) >= 3:
                        break
        
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        news_items = [('Парсинг не удался', '')]
    
    print(f"✅ НАЙДЕНО: {len(news_items)} новостей")
    return {
        'topic': site_config['name'],
        'news_items': news_items[:5]
    }


def print_news(news_data, browser_name):
    print("\n" + "═"*90)
    print(f"📰  QUICKTAB | {browser_name} | {news_data['topic']}")
    print("═"*90)
    
    if len(news_data['news_items']) == 1 and news_data['news_items'][0][0] in ['Сессия потеряна', 'Загрузка недоступна']:
        print(f"⚠️  {news_data['news_items'][0][0]}")
    else:
        for i, (title, url) in enumerate(news_data['news_items'], 1):
            marker = "🔗" if url and url.startswith('http') else "📄"
            
            if url and url.startswith('http'):
                url_display = url.replace('https://ria.ru/', 'ria.ru/') 
                if len(url_display) > 60:
                    url_display = url_display[:57] + "..."
            else:
                url_display = "нет ссылки"
                
            print(f"{i:2d}. {marker} {title}")
            print(f"     📎 {url_display}")
    
    print("═"*90)

def safe_refresh(driver):
    if not safe_driver_check(driver):
        return False
    try:
        driver.refresh()
        time.sleep(3)
        return True
    except:
        return False

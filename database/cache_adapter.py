"""
Cache Adapter for QuickTab
Прозрачная интеграция DatabaseManager с существующими модулями
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .db_manager import DatabaseManager
from .models import WeatherCache, CurrencyCache


class QuickTabCache:
    """
    Адаптер кэша для существующих модулей.
    Заменяет in-memory кэш на SQLite с TTL.
    """
    
    def __init__(self):
        self.db = DatabaseManager()
    
    # ==================== WEATHER ====================
    
    def get_weather(self, city: str) -> Optional[Dict[str, str]]:
        """Получить погоду из кэша"""
        cached = self.db.get_weather_cache(city)
        if cached and not cached.is_expired():
            return {
                'city': cached.city,
                'temp': cached.temperature,
                'desc': cached.description,
                'wind': cached.wind,
                'humidity': cached.humidity,
                'weather_code': cached.weather_code
            }
        return None
    
    def set_weather(self, city: str, data: Dict[str, str], ttl_minutes: int = 30):
        """Сохранить погоду в кэш"""
        self.db.set_weather_cache(
            city=city,
            temp=data.get('temp', ''),
            desc=data.get('desc', ''),
            wind=data.get('wind', ''),
            humidity=data.get('humidity', ''),
            weather_code=data.get('weather_code'),
            ttl_minutes=ttl_minutes
        )
    
    # ==================== CURRENCY ====================
    
    def get_currency(self) -> Optional[Dict[str, str]]:
        """Получить курсы валют из кэша"""
        cached = self.db.get_currency_cache()
        if cached and not cached.is_expired():
            return {
                'USD': cached.usd_rate,
                'EUR': cached.eur_rate,
                'BTC': cached.btc_rate
            }
        return None
    
    def set_currency(self, data: Dict[str, str], ttl_minutes: int = 60):
        """Сохранить курсы валют"""
        self.db.set_currency_cache(
            usd=data.get('USD', ''),
            eur=data.get('EUR', ''),
            btc=data.get('BTC', ''),
            ttl_minutes=ttl_minutes
        )
    
    # ==================== NEWS ====================
    
    def get_news(self, topic: str) -> Optional[List[Dict]]:
        """Получить новости из кэша"""
        articles = self.db.get_news_articles(topic, limit=10)
        if articles:
            # Проверяем свежесть (последние 5 минут)
            latest = max(a.fetched_at for a in articles)
            if datetime.now() - latest < timedelta(minutes=5):
                return [{
                    'title': a.title,
                    'summary': a.summary,
                    'url': a.url,
                    'source': a.source
                } for a in articles]
        return None
    
    def set_news(self, topic: str, articles: List[Dict]):
        """Сохранить новости"""
        self.db.save_news_articles(topic, articles)
    
    # ==================== GENERIC CACHE ====================
    
    def get(self, key: str, cache_type: str) -> Optional[Dict]:
        """Универсальный getter"""
        entry = self.db.get_cache(key, cache_type)
        if entry:
            return entry.get_data_dict()
        return None
    
    def set(self, key: str, cache_type: str, data: Dict, ttl_seconds: int = 300):
        """Универсальный setter"""
        self.db.set_cache(key, cache_type, data, ttl_seconds)
    
    def clear(self, cache_type: Optional[str] = None):
        """Очистить кэш"""
        if cache_type:
            self.db.clear_cache_by_type(cache_type)
        else:
            self.db.clear_expired_cache()


# Глобальный экземпляр для импорта
cache = QuickTabCache()
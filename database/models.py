"""
Database models for QuickTab
SQLAlchemy-style dataclasses with type hints
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import json


@dataclass
class SearchHistory:
    """История поисковых запросов"""
    id: Optional[int] = None
    query: str = ""
    query_type: str = "general"  # general, weather, currency, news, ai
    result_summary: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    click_count: int = 0
    is_favorite: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'query': self.query,
            'query_type': self.query_type,
            'result_summary': self.result_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'click_count': self.click_count,
            'is_favorite': self.is_favorite
        }


@dataclass
class FavoriteSite:
    """Избранные сайты пользователя"""
    id: Optional[int] = None
    title: str = ""
    url: str = ""
    icon: str = ""
    category: str = "other"  # social, news, video, work, shop, other
    color: str = "#FECA57"
    position: int = 0
    click_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'icon': self.icon,
            'category': self.category,
            'color': self.color,
            'position': self.position,
            'click_count': self.click_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }


@dataclass
class UserSettings:
    """Пользовательские настройки (синхронизация с JSON)"""
    id: Optional[int] = None
    theme: str = "Тёмная"
    color_scheme: str = "Синяя"
    font_scale: float = 1.0
    default_city: str = "Белореченск"
    auto_update_interval: int = 5
    cache_enabled: bool = True
    animations_enabled: bool = True
    headless_mode: bool = True
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'theme': self.theme,
            'color_scheme': self.color_scheme,
            'font_scale': self.font_scale,
            'default_city': self.default_city,
            'auto_update_interval': self.auto_update_interval,
            'cache_enabled': self.cache_enabled,
            'animations_enabled': self.animations_enabled,
            'headless_mode': self.headless_mode,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class CacheEntry:
    """Универсальный кэш с TTL"""
    id: Optional[int] = None
    cache_key: str = ""
    cache_type: str = ""  # weather, currency, news, ai_response
    data: str = ""  # JSON serialized
    expires_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    def get_data_dict(self) -> Dict[str, Any]:
        """Deserialize JSON data"""
        try:
            return json.loads(self.data)
        except:
            return {}
    
    def set_data_dict(self, data: Dict[str, Any]):
        """Serialize dict to JSON"""
        self.data = json.dumps(data, ensure_ascii=False)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'cache_type': self.cache_type,
            'data': self.get_data_dict(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'access_count': self.access_count
        }


@dataclass
class NewsArticle:
    """Кэшированные новости"""
    id: Optional[int] = None
    topic: str = ""  # cyber, politics, economy, tech
    title: str = ""
    summary: str = ""
    url: str = ""
    source: str = ""
    published_at: Optional[datetime] = None
    fetched_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'topic': self.topic,
            'title': self.title,
            'summary': self.summary,
            'url': self.url,
            'source': self.source,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
            'is_read': self.is_read
        }


@dataclass
class WeatherCache:
    """Кэш погоды по городам"""
    id: Optional[int] = None
    city: str = ""
    temperature: str = ""
    description: str = ""
    wind: str = ""
    humidity: str = ""
    weather_code: Optional[int] = None
    fetched_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'city': self.city,
            'temperature': self.temperature,
            'description': self.description,
            'wind': self.wind,
            'humidity': self.humidity,
            'weather_code': self.weather_code,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class CurrencyCache:
    """Кэш курсов валют"""
    id: Optional[int] = None
    usd_rate: str = ""
    eur_rate: str = ""
    btc_rate: str = ""
    fetched_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'usd_rate': self.usd_rate,
            'eur_rate': self.eur_rate,
            'btc_rate': self.btc_rate,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class AIConversation:
    """История диалогов с ИИ"""
    id: Optional[int] = None
    session_id: str = ""  # UUID для группировки диалога
    user_query: str = ""
    ai_response: str = ""
    context: str = ""  # Предыдущий контекст
    model_used: str = "deepseek/deepseek-chat"
    response_time_ms: int = 0
    tokens_used: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_clarification: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_query': self.user_query,
            'ai_response': self.ai_response[:200] + '...' if len(self.ai_response) > 200 else self.ai_response,
            'context_length': len(self.context),
            'model_used': self.model_used,
            'response_time_ms': self.response_time_ms,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_clarification': self.is_clarification
        }


@dataclass
class AppStats:
    """Статистика использования приложения"""
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD
    searches_count: int = 0
    weather_requests: int = 0
    currency_requests: int = 0
    news_requests: int = 0
    ai_requests: int = 0
    app_launches: int = 0
    total_session_time_minutes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'date': self.date,
            'searches_count': self.searches_count,
            'weather_requests': self.weather_requests,
            'currency_requests': self.currency_requests,
            'news_requests': self.news_requests,
            'ai_requests': self.ai_requests,
            'app_launches': self.app_launches,
            'total_session_time_minutes': self.total_session_time_minutes
        }
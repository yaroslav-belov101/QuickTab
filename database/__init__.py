"""
Database package for QuickTab
SQLite-based storage with async support
"""

from .db_manager import DatabaseManager
from .models import (
    SearchHistory,
    FavoriteSite,
    UserSettings,
    CacheEntry,
    NewsArticle,
    WeatherCache,
    CurrencyCache,
    AIConversation,
    AppStats
)

__all__ = [
    'DatabaseManager',
    'SearchHistory',
    'FavoriteSite', 
    'UserSettings',
    'CacheEntry',
    'NewsArticle',
    'WeatherCache',
    'CurrencyCache',
    'AIConversation',
    'AppStats'
]
"""
Модули парсинга данных с внешних источников
"""

from .news import get_news_data
from .weather import get_weather_data
from .currency import get_currency_data

__all__ = ['get_news_data', 'get_weather_data', 'get_currency_data']
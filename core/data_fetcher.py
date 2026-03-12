"""
Получение данных из модулей парсинга
"""

from typing import Union, Tuple, List, Dict, Any, Optional
import concurrent.futures

class DataFetcher:
    """
    Получает данные из различных модулей.
    Абстрагирует логику вызова модулей от GUI.
    """
    
    # Маппинг тем новостей
    TOPIC_MAP = {
        "🛡️ Кибербезопасность": "cyber",
        "🌍 Политика": "politics",
        "💰 Экономика": "economy",
        "🚀 Технологии": "tech"
    }
    
    def __init__(self, driver=None):
        self.driver = driver
    
    def fetch(self, module_info: Union[str, Tuple[str, str]]) -> str:
        """
        Получает данные от указанного модуля
        
        Args:
            module_info: Имя модуля или кортеж (модуль, параметр)
            
        Returns:
            Отформатированная строка с результатами
        """
        if isinstance(module_info, tuple):
            module, param = module_info
        else:
            module, param = module_info, None
        
        # Нормализуем параметр темы новостей
        if param in self.TOPIC_MAP:
            param = self.TOPIC_MAP[param]
        
        if module == "weather":
            return self.fetch_weather()
        elif module == "currency":
            return self.fetch_currency()
        elif module == "news":
            return self.fetch_news(param)
        else:
            return f"❌ Неизвестный модуль: {module}\n\n"
    
    def fetch_weather(self) -> str:
        """Получает данные о погоде"""
        from modules.weather import get_weather_data, format_weather_for_display
        
        data = get_weather_data(self.driver)
        return format_weather_for_display(data)
    
    def fetch_currency(self) -> str:
        """Получает курсы валют"""
        from modules.currency import get_currency_data, format_currency_for_display
        
        data = get_currency_data(self.driver)
        return format_currency_for_display(data)
    
    def fetch_news(self, topic: str = "cyber") -> str:
        """Получает новости по теме"""
        from modules.news import get_news_data, format_news_for_display
        
        # Получаем имя темы для отображения
        topic_names = {
            "cyber": "КИБЕРБЕЗОПАСНОСТЬ",
            "politics": "ПОЛИТИКА",
            "economy": "ЭКОНОМИКА",
            "tech": "ТЕХНОЛОГИИ"
        }
        topic_name = topic_names.get(topic, topic.upper())
        
        data = get_news_data(self.driver, topic)
        return format_news_for_display(data, topic_name)
    
    def fetch_parallel(self, modules: list) -> str:
        """Параллельная загрузка всех модулей"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_module = {
                executor.submit(self.fetch, m): m for m in modules
            }
            for future in concurrent.futures.as_completed(future_to_module):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(f"Ошибка: {e}")
        
        return "".join(results)
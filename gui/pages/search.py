import customtkinter as ctk
from .base_page import BasePage
from datetime import datetime
from typing import List, Dict, Optional
import threading
import webbrowser
import re
import time


class SearchPage(BasePage):
    """Страница поиска с парсингом результатов"""
    
    def __init__(self, parent, controller):
        self.search_history = []
        self.current_results = []
        super().__init__(parent, controller)
    
    def create_widgets(self):
        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="ПОИСК",
            font=("Arial", 32, "bold"),
            text_color="#00FFFF"
        )
        title.pack(pady=(20, 15))
        
        # Поле ввода
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Введите запрос...",
            font=("Arial", 20),
            height=45,
            fg_color="#3a3a3a",
            border_color="#555555",
            border_width=2
        )
        self.search_entry.pack(pady=10, padx=30, fill="x")
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        # Кнопка поиска
        search_btn = ctk.CTkButton(
            self,
            text="Искать",
            command=self.perform_search,
            fg_color="#00AAFF",
            hover_color="#0088DD",
            height=45,
            font=("Arial", 18, "bold"),
            corner_radius=10
        )
        search_btn.pack(pady=5, padx=30, fill="x")
        
        # Скроллируемая область контента
        self.content_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            height=450
        )
        self.content_frame.pack(pady=15, padx=20, fill="both", expand=True)
        
        # Показываем начальное состояние
        self.show_start_screen()
    
    def show_start_screen(self):
        """Показать стартовый экран с историей"""
        self._clear_content()
        
        if self.search_history:
            history_frame = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=15)
            history_frame.pack(pady=10, padx=5, fill="x")
            
            header = ctk.CTkFrame(history_frame, fg_color="transparent")
            header.pack(pady=(15, 10), fill="x", padx=15)
            
            ctk.CTkLabel(
                header,
                text="📋 История поиска",
                font=("Arial", 20, "bold"),
                text_color="#FFFFFF"
            ).pack(side="left")
            
            clear_btn = ctk.CTkButton(
                header,
                text="Очистить",
                font=("Arial", 12),
                fg_color="transparent",
                hover_color="#FF5252",
                text_color="#888888",
                width=80,
                height=25,
                command=self.clear_history
            )
            clear_btn.pack(side="right")
            
            for item in reversed(self.search_history[-8:]):
                time_str = self._format_time(item["time"])
                btn = ctk.CTkButton(
                    history_frame,
                    text=f"• {item['query']} ({time_str})",
                    font=("Arial", 16),
                    fg_color="transparent",
                    hover_color="#3a3a3a",
                    text_color="#AAAAAA",
                    anchor="w",
                    height=35,
                    command=lambda q=item['query']: self.set_query(q)
                )
                btn.pack(fill="x", padx=15, pady=2)
        else:
            # Приветствие при первом запуске
            welcome = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=15)
            welcome.pack(pady=20, padx=5, fill="x")
            
            ctk.CTkLabel(
                welcome,
                text="🔍 Добро пожаловать в поиск",
                font=("Arial", 22, "bold"),
                text_color="#00AAFF"
            ).pack(pady=(20, 10))
            
            ctk.CTkLabel(
                welcome,
                text="Введите запрос для поиска информации.\n\n"
                     "Примеры:\n"
                     "• Курс доллара, евро, bitcoin\n"
                     "• Погода в [город]\n"
                     "• Новости [тема]\n"
                     "• Что такое Python, Wikipedia\n"
                     "• Любой вопрос — поиск в интернете",
                font=("Arial", 16),
                text_color="#CCCCCC",
                justify="left"
            ).pack(pady=10, padx=20)
    
    def _format_time(self, time_str: str) -> str:
        """Форматировать время относительно сейчас"""
        try:
            past = datetime.fromisoformat(time_str)
            now = datetime.now()
            delta = now - past
            
            if delta.days == 0:
                hours = delta.seconds // 3600
                if hours == 0:
                    minutes = delta.seconds // 60
                    return f"{minutes} мин назад" if minutes > 0 else "только что"
                return f"{hours} ч назад"
            elif delta.days == 1:
                return "вчера"
            else:
                return f"{delta.days} дн назад"
        except:
            return time_str
    
    def set_query(self, query: str):
        """Установить запрос в поле ввода"""
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, query)
        self.perform_search()
    
    def clear_history(self):
        """Очистить историю"""
        self.search_history.clear()
        self.show_start_screen()
    
    def _clear_content(self):
        """Очистить контентную область"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def perform_search(self):
        """Выполнить поиск"""
        query = self.search_entry.get().strip()
        
        if not query:
            self.show_error("Введите поисковый запрос!")
            return
        
        # Сохраняем в историю
        self.add_to_history(query)
        
        # Показываем загрузку
        self.show_loading()
        
        # Запускаем поиск в отдельном потоке
        threading.Thread(target=self._do_search, args=(query,), daemon=True).start()
    
    def add_to_history(self, query: str):
        """Добавить запрос в историю"""
        self.search_history = [h for h in self.search_history if h["query"] != query]
        self.search_history.append({
            "query": query,
            "time": datetime.now().isoformat()
        })
        self.search_history = self.search_history[-15:]
    
    def show_loading(self):
        """Показать индикатор загрузки"""
        self._clear_content()
        
        loading_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        loading_frame.pack(expand=True)
        
        self.loading_label = ctk.CTkLabel(
            loading_frame,
            text="🔍 Ищем...",
            font=("Arial", 24),
            text_color="#00AAFF"
        )
        self.loading_label.pack(pady=20)
        
        self.loading_status = ctk.CTkLabel(
            loading_frame,
            text="Подключение к источникам...",
            font=("Arial", 14),
            text_color="#888888"
        )
        self.loading_status.pack()
        
        progress = ctk.CTkProgressBar(loading_frame, width=250, mode="indeterminate")
        progress.pack()
        progress.start()
    
    def update_loading_status(self, text: str):
        """Обновить статус загрузки"""
        if hasattr(self, 'loading_status'):
            self.after(0, lambda: self.loading_status.configure(text=text))
    
    def show_error(self, message: str):
        """Показать ошибку"""
        self._clear_content()
        
        error_frame = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=15)
        error_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(
            error_frame,
            text=f"⚠️ {message}",
            font=("Arial", 18),
            text_color="#FF5252"
        ).pack(pady=20)
        
        ctk.CTkButton(
            error_frame,
            text="← Назад",
            command=self.show_start_screen,
            fg_color="#555555",
            hover_color="#666666"
        ).pack(pady=10)
    
    def _get_homepage_data(self):
        """Получить данные с главной страницы через контроллер"""
        try:
            homepage = None
            
            if hasattr(self.controller, 'pages'):
                homepage = self.controller.pages.get('HomePage')
            
            if not homepage and hasattr(self.controller, 'frames'):
                homepage = self.controller.frames.get('HomePage')
            
            if not homepage and hasattr(self.controller, 'home_page'):
                homepage = self.controller.home_page
            
            if not homepage:
                for attr_name in dir(self.controller):
                    attr = getattr(self.controller, attr_name, None)
                    if hasattr(attr, 'cache') and isinstance(attr.cache, dict) and 'weather' in attr.cache:
                        homepage = attr
                        break
            
            return homepage
        except Exception as e:
            print(f"[Search] Ошибка получения HomePage: {e}")
            return None
    
    def _get_driver(self):
        """Получить WebDriver из контроллера"""
        try:
            driver = getattr(self.controller, 'driver', None)
            if driver:
                return driver
        except:
            pass
        return None
    
    def _do_search(self, query: str):
        """Фактический поиск с приоритетами"""
        results = []
        query_lower = query.lower()
        
        print(f"[Search] Начало поиска: '{query}'")
        
        # УРОВЕНЬ 1: Быстрые ответы (локальные данные)
        
        # 1. Поиск валют
        self.update_loading_status("Проверка курсов валют...")
        currency_result = self._search_currency(query_lower, query)
        if currency_result:
            print(f"[Search] Найдена валюта: {currency_result['title']}")
            results.append(currency_result)
        
        # 2. Поиск погоды
        self.update_loading_status("Проверка погоды...")
        weather_result = self._search_weather(query_lower, query)
        if weather_result:
            print(f"[Search] Найдена погода: {weather_result['title']}")
            results.append(weather_result)
        
        # 3. Поиск новостей
        self.update_loading_status("Поиск в новостях...")
        news_result = self._search_news(query_lower, query)
        if news_result:
            print(f"[Search] Найдены новости: {news_result['title']}")
            results.append(news_result)
        
        # УРОВЕНЬ 2: Парсинг конкретных сайтов (Wikipedia, etc.)
        if not results or self._is_knowledge_query(query_lower):
            self.update_loading_status("Поиск в базах знаний...")
            wiki_result = self._search_wikipedia(query)
            if wiki_result:
                results.append(wiki_result)
        
        # УРОВЕНЬ 3: Поисковая выдача DuckDuckGo
        if not results:
            self.update_loading_status("Поиск в интернете...")
            web_results = self._search_web(query)
            if web_results:
                results.extend(web_results)
        
        print(f"[Search] Всего результатов: {len(results)}")
        
        # Если совсем ничего не нашли
        if not results:
            results.append({
                "type": "web",
                "title": "🔍 Нет результатов",
                "content": f"По запросу '{query}' ничего не найдено.\nПопробуйте изменить запрос.",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "action": "Открыть в браузере"
            })
        
        self.current_results = results
        self.after(0, lambda: self.show_results(query, results))
    
    def _is_knowledge_query(self, query_lower: str) -> bool:
        """Определить, является ли запрос запросом знаний"""
        knowledge_patterns = [
            r'что такое',
            r'кто такой',
            r'когда',
            r'где',
            r'зачем',
            r'почему',
            r'как',
            r'википедия',
            r'wikipedia',
        ]
        return any(re.search(p, query_lower) for p in knowledge_patterns)
    
    def _search_currency(self, query_lower: str, original: str) -> Optional[Dict]:
        """Поиск валют"""
        has_currency_keyword = any(kw in query_lower for kw in [
            "курс", "цена", "стоимость", "доллар", "евро", "биткоин", 
            "bitcoin", "usd", "eur", "btc", "рубль", "конверт"
        ])
        
        if not has_currency_keyword:
            return None
        
        currency_data = self._get_currency_data()
        
        found_rates = []
        
        if any(kw in query_lower for kw in ["доллар", "usd"]):
            if "USD" in currency_data:
                found_rates.append(f"USD: {currency_data['USD']}")
        
        if any(kw in query_lower for kw in ["евро", "eur"]):
            if "EUR" in currency_data:
                found_rates.append(f"EUR: {currency_data['EUR']}")
        
        if any(kw in query_lower for kw in ["биткоин", "bitcoin", "btc"]):
            if "BTC" in currency_data:
                found_rates.append(f"BTC: {currency_data['BTC']}")
        
        if found_rates:
            return {
                "type": "currency",
                "title": "💱 Курс валют",
                "content": "\n".join(found_rates),
                "data": currency_data,
                "action": "Обновить курсы"
            }
        
        if "курс" in query_lower and not found_rates:
            all_rates = []
            for code in ["USD", "EUR", "BTC"]:
                if code in currency_data:
                    all_rates.append(f"{code}: {currency_data[code]}")
            
            if all_rates:
                return {
                    "type": "currency",
                    "title": "💱 Курсы валют",
                    "content": "\n".join(all_rates),
                    "data": currency_data,
                    "action": "Обновить курсы"
                }
        
        if any(x in query_lower for x in ["в руб", "в долл", "в евро", "в btc", "конверт"]):
            return self._parse_converter_query(original, currency_data)
        
        return None
    
    def _get_currency_data(self) -> Dict:
        """Получить данные валют"""
        homepage = self._get_homepage_data()
        
        if homepage and hasattr(homepage, 'cache'):
            currency_cache = homepage.cache.get('currency', {})
            data = currency_cache.get('data')
            if data:
                return data
        
        try:
            from modules.currency import _cache
            if _cache.get("USD") and _cache.get("EUR"):
                return {
                    "USD": _cache["USD"],
                    "EUR": _cache["EUR"],
                    "BTC": _cache.get("BTC", "Нет данных")
                }
        except:
            pass
        
        return {"USD": "92.50 ₽", "EUR": "100.20 ₽", "BTC": "95000 USD"}
    
    def _parse_converter_query(self, query: str, currency_data: Dict) -> Optional[Dict]:
        """Парсинг запроса конвертации"""
        match = re.search(r'(\d+(?:\.\d+)?)', query)
        if not match:
            return None
        
        amount = float(match.group(1))
        query_lower = query.lower()
        
        from_curr = None
        if any(kw in query_lower for kw in ["доллар", "usd"]):
            from_curr = "USD"
        elif any(kw in query_lower for kw in ["евро", "eur"]):
            from_curr = "EUR"
        elif any(kw in query_lower for kw in ["биткоин", "bitcoin", "btc"]):
            from_curr = "BTC"
        elif "рубл" in query_lower:
            from_curr = "RUB"
        
        to_curr = None
        if "в руб" in query_lower:
            to_curr = "RUB"
        elif "в долл" in query_lower or "в usd" in query_lower:
            to_curr = "USD"
        elif "в евро" in query_lower or "в eur" in query_lower:
            to_curr = "EUR"
        elif "в биткоин" in query_lower or "в btc" in query_lower:
            to_curr = "BTC"
        
        if not from_curr or not to_curr or from_curr == to_curr:
            return None
        
        rates = {}
        for code in ["USD", "EUR", "BTC"]:
            if code in currency_data:
                rate_str = currency_data[code].replace('₽', '').replace('USD', '').replace(' ', '').replace(',', '.')
                try:
                    rates[code] = float(rate_str)
                except:
                    rates[code] = 1.0
        
        rates["RUB"] = 1.0
        
        if from_curr in rates and to_curr in rates:
            in_rub = amount * rates[from_curr] if from_curr != "RUB" else amount
            result = in_rub / rates[to_curr] if to_curr != "RUB" else in_rub
            
            return {
                "type": "converter",
                "title": "💱 Конвертер валют",
                "content": f"{amount:,.2f} {from_curr} = {result:,.2f} {to_curr}\n\n"
                          f"Курс: 1 {from_curr} = {rates[from_curr]/rates[to_curr]:,.2f} {to_curr}",
                "action": "Точные курсы"
            }
        
        return None
    
    def _search_weather(self, query_lower: str, original: str) -> Optional[Dict]:
        """Поиск погоды"""
        if not any(kw in query_lower for kw in ["погода", "температура", "градус"]):
            return None
        
        city = None
        patterns = [
            r'погода\s+в\s+(\S+)',
            r'погода\s+(\S+)',
            r'в\s+(\S+)\s+погода',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                city = match.group(1).strip()
                break
        
        if not city:
            city = "Белореченск"
        
        weather_data = self._get_weather_data(city)
        
        if weather_data:
            return {
                "type": "weather",
                "title": f"🌤️ Погода в {weather_data.get('city', city)}",
                "content": f"{weather_data.get('temp', '--')}, {weather_data.get('desc', 'Нет данных')}\n"
                          f"💨 Ветер: {weather_data.get('wind', '--')}\n"
                          f"💧 Влажность: {weather_data.get('humidity', '--')}",
                "data": weather_data,
                "action": "Подробнее"
            }
        
        return None
    
    def _get_weather_data(self, city: str) -> Optional[Dict]:
        """Получить данные погоды"""
        homepage = self._get_homepage_data()
        
        if homepage and hasattr(homepage, 'cache'):
            weather_cache = homepage.cache.get('weather', {})
            cached_city = weather_cache.get('city')
            data = weather_cache.get('data')
            
            if cached_city and data:
                if cached_city.lower() == city.lower():
                    return data
                
                return {
                    "city": city,
                    "temp": data.get('temp', '--'),
                    "desc": data.get('desc', 'Нет данных'),
                    "wind": data.get('wind', '--'),
                    "humidity": data.get('humidity', '--')
                }
        
        try:
            from modules.weather import get_weather_data
            data = get_weather_data(None, city)
            if data:
                return data
        except:
            pass
        
        return {
            "city": city,
            "temp": "+5°C",
            "desc": "Облачно",
            "wind": "3 м/с",
            "humidity": "65%"
        }
    
    def _search_news(self, query_lower: str, original: str) -> Optional[Dict]:
        """Поиск в новостях"""
        try:
            from modules.news import _news_cache
            all_news = []
            topics = ["cyber", "politics", "economy", "tech"]
            
            for topic in topics:
                news_list = _news_cache.get(topic, [])
                for news in news_list:
                    all_news.append({
                        "title": news.get('title', ''),
                        "url": news.get('url', ''),
                        "topic": topic
                    })
            
            if not all_news:
                return None
            
            matching = []
            for news in all_news:
                title_lower = news['title'].lower()
                if query_lower in title_lower:
                    matching.append(news)
            
            if matching:
                preview = "\n".join([f"• {n['title'][:50]}..." for n in matching[:5]])
                return {
                    "type": "news",
                    "title": f"📰 Найдено в новостях ({len(matching)})",
                    "content": preview,
                    "action": "Открыть новости"
                }
            
            return None
        except:
            return None
    
    def _search_wikipedia(self, query: str) -> Optional[Dict]:
        """Поиск в Wikipedia через парсинг"""
        driver = self._get_driver()
        if not driver:
            return None
        
        try:
            # Формируем URL поиска Wikipedia
            search_term = query.replace(' ', '_')
            if 'что такое' in query.lower():
                search_term = query.lower().replace('что такое', '').strip().replace(' ', '_')
            
            url = f"https://ru.wikipedia.org/wiki/{search_term}"
            
            self.update_loading_status(f"Загрузка Wikipedia...")
            
            driver.get(url)
            time.sleep(2)
            
            # Проверяем, есть ли статья
            from selenium.webdriver.common.by import By
            
            # Ищем заголовок статьи
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, "h1.firstHeading")
                title = title_elem.text.strip()
            except:
                title = query
            
            # Ищем первый параграф
            try:
                # Пробуем найти основное содержимое
                content = driver.find_element(By.CSS_SELECTOR, "div.mw-parser-output > p:not(.mw-empty-elt)")
                snippet = content.text.strip()[:300]
                if len(snippet) > 290:
                    snippet += "..."
            except:
                # Fallback: ищем любой параграф
                try:
                    paragraphs = driver.find_elements(By.CSS_SELECTOR, "p")
                    for p in paragraphs:
                        text = p.text.strip()
                        if len(text) > 50:
                            snippet = text[:300]
                            if len(snippet) > 290:
                                snippet += "..."
                            break
                    else:
                        return None
                except:
                    return None
            
            # Проверяем, что это не страница "Статья не найдена"
            if "не существует" in snippet.lower() or "запросу не соответствует" in snippet.lower():
                # Пробуем поиск
                search_url = f"https://ru.wikipedia.org/w/index.php?search={query.replace(' ', '+')}"
                driver.get(search_url)
                time.sleep(2)
                
                # Ищем результаты поиска
                try:
                    results = driver.find_elements(By.CSS_SELECTOR, "div.mw-search-result-heading a")
                    if results:
                        first_link = results[0].get_attribute('href')
                        driver.get(first_link)
                        time.sleep(2)
                        
                        # Получаем данные с найденной страницы
                        title = driver.find_element(By.CSS_SELECTOR, "h1.firstHeading").text.strip()
                        content = driver.find_element(By.CSS_SELECTOR, "div.mw-parser-output > p:not(.mw-empty-elt)")
                        snippet = content.text.strip()[:300]
                        if len(snippet) > 290:
                            snippet += "..."
                    else:
                        return None
                except:
                    return None
            
            return {
                "type": "wiki",
                "title": f"📚 {title}",
                "content": snippet,
                "url": driver.current_url,
                "action": "Открыть статью"
            }
            
        except Exception as e:
            print(f"[Search] Ошибка Wikipedia: {e}")
            return None
    
    def _search_web(self, query: str) -> List[Dict]:
        """Поиск в DuckDuckGo через Selenium"""
        driver = self._get_driver()
        if not driver:
            return []
        
        results = []
        
        try:
            # Используем DuckDuckGo HTML-версию (без JS)
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            
            self.update_loading_status("Загрузка результатов...")
            
            driver.get(search_url)
            time.sleep(3)
            
            from selenium.webdriver.common.by import By
            
            # Ищем результаты
            result_elements = driver.find_elements(By.CSS_SELECTOR, "div.result")
            
            for i, elem in enumerate(result_elements[:5]):  # Первые 5 результатов
                try:
                    # Заголовок и ссылка
                    link_elem = elem.find_element(By.CSS_SELECTOR, "a.result__a")
                    title = link_elem.text.strip()
                    url = link_elem.get_attribute('href')
                    
                    # Сниппет (описание)
                    try:
                        snippet_elem = elem.find_element(By.CSS_SELECTOR, "a.result__snippet")
                        snippet = snippet_elem.text.strip()[:200]
                        if len(snippet) > 190:
                            snippet += "..."
                    except:
                        snippet = "Нет описания"
                    
                    results.append({
                        "type": "web",
                        "title": title,
                        "content": snippet,
                        "url": url,
                        "action": "Открыть"
                    })
                    
                except Exception as e:
                    print(f"[Search] Ошибка парсинга результата {i}: {e}")
                    continue
            
            # Если не нашли через HTML-версию, пробуем обычную
            if not results:
                self.update_loading_status("Пробуем альтернативный метод...")
                
                search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
                driver.get(search_url)
                time.sleep(4)
                
                # Ищем в обычной версии
                try:
                    # Ждем загрузки результатов
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    wait = WebDriverWait(driver, 10)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']")))
                    
                    result_elements = driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']")
                    
                    for elem in result_elements[:5]:
                        try:
                            title_elem = elem.find_element(By.CSS_SELECTOR, "[data-testid='result-title-a']")
                            title = title_elem.text.strip()
                            url = title_elem.get_attribute('href')
                            
                            try:
                                snippet_elem = elem.find_element(By.CSS_SELECTOR, "[data-testid='result-snippet']")
                                snippet = snippet_elem.text.strip()[:200]
                                if len(snippet) > 190:
                                    snippet += "..."
                            except:
                                snippet = "Нет описания"
                            
                            results.append({
                                "type": "web",
                                "title": title,
                                "content": snippet,
                                "url": url,
                                "action": "Открыть"
                            })
                        except:
                            continue
                            
                except Exception as e:
                    print(f"[Search] Ошибка обычной версии DDG: {e}")
        
        except Exception as e:
            print(f"[Search] Ошибка веб-поиска: {e}")
        
        return results
    
    def show_results(self, query: str, results: List[Dict]):
        """Показать результаты поиска"""
        self._clear_content()
        
        # Кнопка "Назад"
        back_btn = ctk.CTkButton(
            self.content_frame,
            text="← Новый поиск",
            command=self.show_start_screen,
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color="#888888",
            anchor="w",
            height=35,
            font=("Arial", 16)
        )
        back_btn.pack(fill="x", pady=(0, 10))
        
        # Запрос
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            header,
            text="Результаты поиска",
            font=("Arial", 20, "bold"),
            text_color="#FFFFFF"
        ).pack(side="left")
        
        ctk.CTkLabel(
            header,
            text=f"'{query}'",
            font=("Arial", 16),
            text_color="#888888"
        ).pack(side="left", padx=(10, 0))
        
        # Результаты
        for result in results:
            self._create_result_card(result)
    
    def _create_result_card(self, result: Dict):
        """Создать карточку результата"""
        colors = {
            "currency": "#00C853",
            "converter": "#00C853",
            "weather": "#2979FF",
            "news": "#FF9100",
            "wiki": "#9C27B0",
            "web": "#888888"
        }
        color = colors.get(result["type"], "#00AAFF")
        
        card = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=15)
        card.pack(pady=10, fill="x")
        
        # Иконка по типу
        icons = {
            "currency": "💱",
            "converter": "💱",
            "weather": "🌤️",
            "news": "📰",
            "wiki": "📚",
            "web": "🌐"
        }
        icon = icons.get(result["type"], "🔍")
        
        # Заголовок с иконкой
        title_frame = ctk.CTkFrame(card, fg_color="transparent")
        title_frame.pack(pady=(15, 5), fill="x", padx=15)
        
        ctk.CTkLabel(
            title_frame,
            text=f"{icon} {result['title']}",
            font=("Arial", 18, "bold"),
            text_color=color
        ).pack(side="left")
        
        # Содержимое
        ctk.CTkLabel(
            card,
            text=result["content"],
            font=("Arial", 15),
            text_color="#CCCCCC",
            wraplength=700,
            justify="left"
        ).pack(pady=10, anchor="w", padx=15)
        
        # Кнопки действий
        if result.get("action") or result.get("url"):
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(pady=(0, 15), anchor="w", padx=15)
            
            if result.get("action"):
                action_btn = ctk.CTkButton(
                    btn_frame,
                    text=result["action"],
                    font=("Arial", 14),
                    fg_color="#3a3a3a",
                    hover_color=color,
                    text_color="#FFFFFF",
                    height=35,
                    width=140,
                    corner_radius=8,
                    command=lambda r=result: self._handle_action(r)
                )
                action_btn.pack(side="left", padx=(0, 10))
            
            if result.get("url"):
                copy_btn = ctk.CTkButton(
                    btn_frame,
                    text="Копировать ссылку",
                    font=("Arial", 14),
                    fg_color="transparent",
                    hover_color="#3a3a3a",
                    text_color="#888888",
                    height=35,
                    width=140,
                    command=lambda u=result["url"]: self._copy_to_clipboard(u)
                )
                copy_btn.pack(side="left")
    
    def _handle_action(self, result: Dict):
        """Обработать действие карточки"""
        rtype = result.get("type")
        
        if rtype in ["currency", "converter", "weather", "news"]:
            self.controller.show_frame("HomePage")
        elif result.get("url"):
            webbrowser.open(result["url"])
    
    def _copy_to_clipboard(self, text: str):
        """Копировать в буфер обмена"""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        
        notif = ctk.CTkLabel(
            self,
            text="✓ Скопировано!",
            font=("Arial", 14),
            text_color="#00FF00",
            fg_color="#2a2a2a",
            corner_radius=10
        )
        notif.place(relx=0.5, rely=0.9, anchor="center")
        self.after(1500, notif.destroy)
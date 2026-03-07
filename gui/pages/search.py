import customtkinter as ctk
from .base_page import BasePage
from datetime import datetime
from typing import List, Dict, Optional
import threading
import webbrowser
import re
import time
import google.generativeai as genai


class SearchPage(BasePage):
    """Страница поиска с краткой сводкой и ссылками"""
    
    def __init__(self, parent, controller):
        self.search_history = []
        self.current_results = []
        self.quick_answer = None
        self.web_links = []
        self.last_ai_query = None  # Для сохранения последнего вопроса к ИИ
        self.ai_context = None  # Для сохранения контекста диалога
        super().__init__(parent, controller)
    
    def create_widgets(self):
        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="ПОИСК",
            font=("Arial", 48, "bold"),
            text_color="#00FFFF"
        )
        title.pack(pady=(20, 15))
        
        # Поле ввода
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Введите запрос...",
            font=("Arial", 30),
            height=68,
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
            height=68,
            font=("Arial", 27, "bold"),
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
        self.quick_answer = None
        self.web_links = []
        
        if self.search_history:
            history_frame = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=15)
            history_frame.pack(pady=10, padx=5, fill="x")
            
            header = ctk.CTkFrame(history_frame, fg_color="transparent")
            header.pack(pady=(15, 10), fill="x", padx=15)
            
            ctk.CTkLabel(
                header,
                text="📋 История поиска",
                font=("Arial", 30, "bold"),
                text_color="#FFFFFF"
            ).pack(side="left")
            
            clear_btn = ctk.CTkButton(
                header,
                text="Очистить",
                font=("Arial", 18),
                fg_color="transparent",
                hover_color="#FF5252",
                text_color="#888888",
                width=120,
                height=38,
                command=self.clear_history
            )
            clear_btn.pack(side="right")
            
            for item in reversed(self.search_history[-8:]):
                time_str = self._format_time(item["time"])
                btn = ctk.CTkButton(
                    history_frame,
                    text=f"• {item['query']} ({time_str})",
                    font=("Arial", 24),
                    fg_color="transparent",
                    hover_color="#3a3a3a",
                    text_color="#AAAAAA",
                    anchor="w",
                    height=52,
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
                font=("Arial", 33, "bold"),
                text_color="#00AAFF"
            ).pack(pady=(20, 10))
            
            ctk.CTkLabel(
                welcome,
                text="Введите запрос для поиска информации.\n\n"
                     "Примеры:\n"
                     "• Курс доллара, евро, bitcoin\n"
                     "• Погода в [город]\n"
                     "• Новости [тема]\n"
                     "• Ответы на вопросы",
                font=("Arial", 24),
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
            font=("Arial", 36),
            text_color="#00AAFF"
        )
        self.loading_label.pack(pady=20)
        
        self.loading_status = ctk.CTkLabel(
            loading_frame,
            text="Формируем краткую сводку...",
            font=("Arial", 21),
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
            font=("Arial", 27),
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
        """Фактический поиск: сначала сводка, потом ссылки"""
        query_lower = query.lower()
        
        print(f"[Search] Начало поиска: '{query}'")
        
        # === ЭТАП 1: Формируем краткую сводку ===
        self.update_loading_status("Формируем краткую сводку...")
        
        quick_answer = self._get_quick_answer(query, query_lower, self.ai_context)
        
        # === ЭТАП 2: Ищем ссылки в интернете ===
        self.update_loading_status("Ищем ссылки в интернете...")
        
        web_links = self._get_web_links(query)
        
        # === ЭТАП 3: Показываем результаты ===
        self.quick_answer = quick_answer
        self.web_links = web_links
        self.last_ai_query = query  # Сохраняем последний запрос
        self.ai_context = None  # Очищаем контекст после использования
        
        self.after(0, lambda: self._display_results(query, quick_answer, web_links))
    
    def _get_quick_answer(self, query: str, query_lower: str, context: Optional[str] = None) -> Optional[Dict]:
        """Получить краткую сводку из всех источников"""
        
        # 1. Валюты
        if any(kw in query_lower for kw in ["курс", "цена", "стоимость", "доллар", "евро", "биткоин", "usd", "eur", "btc"]):
            result = self._search_currency(query_lower, query)
            if result:
                return result
        
        # 2. Погода
        if any(kw in query_lower for kw in ["погода", "температура", "градус"]):
            result = self._search_weather(query_lower, query)
            if result:
                return result
        
        # 3. Новости
        if any(kw in query_lower for kw in ["новост", "событ"]):
            result = self._search_news(query_lower, query)
            if result:
                return result
        
        # 4. Wikipedia для знаний
        if self._is_knowledge_query(query_lower):
            result = self._search_wikipedia(query)
            if result:
                return result
        
        # 5. Калькулятор
        math_result = self._calculate_math(query)
        if math_result:
            return math_result
        
        # 6. ИИ для произвольных вопросов
        ai_result = self._query_gemini(query, context)
        if ai_result:
            return ai_result
        
        return None
    
    def _get_web_links(self, query: str) -> List[Dict]:
        """Получить ссылки из веб-поиска"""
        links = []
        
        # Пробуем DuckDuckGo
        ddg_results = self._search_duckduckgo(query)
        if ddg_results:
            links.extend(ddg_results)
        
        # Если мало результатов, добавляем прямые ссылки на поисковики
        if len(links) < 3:
            links.append({
                "type": "search_engine",
                "title": "🔍 DuckDuckGo",
                "content": "Поискать в DuckDuckGo",
                "url": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                "action": "Открыть"
            })
            links.append({
                "type": "search_engine", 
                "title": "🌐 Google",
                "content": "Поискать в Google",
                "url": f"https://google.com/search?q={query.replace(' ', '+')}",
                "action": "Открыть"
            })
        
        return links[:8]
    
    def _display_results(self, query: str, quick_answer: Optional[Dict], web_links: List[Dict]):
        """Отобразить результаты: сводка сверху, ссылки снизу"""
        self._clear_content()
        
        # Кнопка "Назад" и заголовок
        top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 10))
        
        back_btn = ctk.CTkButton(
            top_frame,
            text="← Новый поиск",
            command=self.show_start_screen,
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color="#888888",
            anchor="w",
            height=52,
            font=("Arial", 24)
        )
        back_btn.pack(side="left")
        
        ctk.CTkLabel(
            top_frame,
            text=f"'{query}'",
            font=("Arial", 24),
            text_color="#888888"
        ).pack(side="right")
        
        # === КРАТКАЯ СВОДКА ===
        if quick_answer:
            self._create_quick_answer_card(quick_answer)
        else:
            no_answer = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=15)
            no_answer.pack(pady=10, fill="x")
            
            ctk.CTkLabel(
                no_answer,
                text="💡 Краткая сводка",
                font=("Arial", 27, "bold"),
                text_color="#888888"
            ).pack(pady=(20, 10), anchor="w", padx=20)
            
            ctk.CTkLabel(
                no_answer,
                text="Нет данных в приложении. Используйте ссылки ниже для поиска в интернете.",
                font=("Arial", 24),
                text_color="#AAAAAA",
                wraplength=700
            ).pack(pady=10, anchor="w", padx=20)
        
        # === РАЗДЕЛИТЕЛЬ ===
        if web_links:
            separator = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            separator.pack(pady=15, fill="x")
            
            ctk.CTkLabel(
                separator,
                text="🔗 ССЫЛКИ",
                font=("Arial", 24, "bold"),
                text_color="#555555"
            ).pack(side="left")
            
            line = ctk.CTkFrame(separator, fg_color="#444444", height=2)
            line.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # === ССЫЛКИ ===
        for link in web_links:
            self._create_link_card(link)
    
    def _create_quick_answer_card(self, answer: Dict):
        """Создать карточку краткой сводки"""
        colors = {
            "currency": "#00C853",
            "converter": "#00C853",
            "weather": "#2979FF",
            "news": "#FF9100",
            "wiki": "#9C27B0",
            "math": "#FF5722",
            "ai": "#FF6D00"
        }
        color = colors.get(answer["type"], "#00AAFF")
        
        icons = {
            "currency": "💱",
            "converter": "💱",
            "weather": "🌤️",
            "news": "📰",
            "wiki": "📚",
            "math": "🧮",
            "ai": "🤖"
        }
        icon = icons.get(answer["type"], "💡")
        
        # Карточка сводки
        card = ctk.CTkFrame(
            self.content_frame, 
            fg_color=color,
            corner_radius=20,
            border_width=0
        )
        card.pack(pady=10, fill="x")
        
        # Внутренняя рамка
        inner = ctk.CTkFrame(card, fg_color="#1a1a1a", corner_radius=18)
        inner.pack(padx=3, pady=3, fill="both", expand=True)
        
        # Заголовок
        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.pack(pady=(20, 10), fill="x", padx=20)
        
        ctk.CTkLabel(
            title_frame,
            text=f"{icon} {answer['title']}",
            font=("Arial", 33, "bold"),
            text_color=color
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="КРАТКАЯ СВОДКА",
            font=("Arial", 18),
            text_color="#666666",
            fg_color="#2a2a2a",
            corner_radius=10
        ).pack(side="right", padx=(10, 0))
        
        # Содержимое
        content = ctk.CTkLabel(
            inner,
            text=answer["content"],
            font=("Arial", 27),
            text_color="#FFFFFF",
            wraplength=680,
            justify="left"
        )
        content.pack(pady=15, anchor="w", padx=20)
        
        # Кнопки
        if answer.get("action"):
            btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
            btn_frame.pack(pady=(0, 20), anchor="w", padx=20)
            
            action_btn = ctk.CTkButton(
                btn_frame,
                text=answer["action"],
                font=("Arial", 24, "bold"),
                fg_color=color,
                hover_color="#FFFFFF",
                text_color="#000000",
                height=68,
                width=270,
                corner_radius=10,
                command=lambda a=answer: self._handle_quick_answer(a)
            )
            action_btn.pack(side="left")
            
            if answer.get("url"):
                copy_btn = ctk.CTkButton(
                    btn_frame,
                    text="🔗 Копировать ссылку",
                    font=("Arial", 21),
                    fg_color="transparent",
                    hover_color="#3a3a3a",
                    text_color="#888888",
                    height=68,
                    command=lambda u=answer["url"]: self._copy_to_clipboard(u)
                )
                copy_btn.pack(side="left", padx=(10, 0))
    
    def _create_link_card(self, link: Dict):
        """Создать карточку ссылки"""
        colors = {
            "web": "#888888",
            "search_engine": "#00AAFF",
            "wiki": "#9C27B0"
        }
        color = colors.get(link["type"], "#888888")
        
        card = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=12)
        card.pack(pady=5, fill="x")
        
        # Заголовок
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(pady=(12, 5), fill="x", padx=15)
        
        ctk.CTkLabel(
            header,
            text=link["title"],
            font=("Arial", 24, "bold"),
            text_color=color
        ).pack(side="left")
        
        # Домен
        if link.get("url"):
            try:
                from urllib.parse import urlparse
                domain = urlparse(link["url"]).netloc.replace("www.", "")
                if domain:
                    ctk.CTkLabel(
                        header,
                        text=f"({domain})",
                        font=("Arial", 18),
                        text_color="#666666"
                    ).pack(side="left", padx=(8, 0))
            except:
                pass
        
        # Сниппет
        if link.get("content"):
            ctk.CTkLabel(
                card,
                text=link["content"],
                font=("Arial", 21),
                text_color="#AAAAAA",
                wraplength=680,
                justify="left"
            ).pack(pady=5, anchor="w", padx=15)
        
        # Кнопки
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=(5, 12), anchor="w", padx=15)
        
        action_btn = ctk.CTkButton(
            btn_frame,
            text=link.get("action", "Открыть"),
            font=("Arial", 20),
            fg_color="#3a3a3a",
            hover_color=color,
            text_color="#FFFFFF",
            height=48,
            width=150,
            corner_radius=6,
            command=lambda l=link: self._open_link(l)
        )
        action_btn.pack(side="left")
        
        if link.get("url"):
            copy_btn = ctk.CTkButton(
                btn_frame,
                text="Копировать",
                font=("Arial", 20),
                fg_color="transparent",
                hover_color="#3a3a3a",
                text_color="#666666",
                height=48,
                width=150,
                command=lambda u=link["url"]: self._copy_to_clipboard(u)
            )
            copy_btn.pack(side="left", padx=(8, 0))
    
    def _handle_quick_answer(self, answer: Dict):
        """Обработать действие краткой сводки"""
        rtype = answer.get("type")
        
        if rtype in ["currency", "converter", "weather", "news"]:
            self.controller.show_frame("HomePage")
        elif rtype == "ai":
            # Для уточнения вопроса: сохраняем контекст и показываем подсказку
            self.ai_context = answer.get("content", "")  # Сохраняем ответ как контекст
            self.search_entry.delete(0, "end")
            self.search_entry.focus()
            # Подсвечиваем, что это уточнение
            hint = ctk.CTkLabel(
                self.content_frame,
                text="💬 Режим уточнения (введите дополнительный вопрос)",
                font=("Arial", 18),
                text_color="#00FF00"
            )
            hint.pack(pady=5)
            self.after(3000, hint.destroy)  # Удалить подсказку через 3 секунды
        elif answer.get("url"):
            webbrowser.open(answer["url"])
    
    def _open_link(self, link: Dict):
        """Открыть ссылку"""
        if link.get("url"):
            webbrowser.open(link["url"])
    
    def _copy_to_clipboard(self, text: str):
        """Копировать в буфер обмена"""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        
        notif = ctk.CTkLabel(
            self,
            text="✓ Скопировано!",
            font=("Arial", 21),
            text_color="#00FF00",
            fg_color="#2a2a2a",
            corner_radius=10
        )
        notif.place(relx=0.5, rely=0.9, anchor="center")
        self.after(1500, notif.destroy)
    
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
    
    def _calculate_math(self, query: str) -> Optional[Dict]:
        """Вычислить математическое выражение"""
        try:
            clean = re.sub(r'[^0-9+\-*/().\s]', '', query)
            if not clean or len(clean) < 3:
                return None
            
            if not any(op in clean for op in ['+', '-', '*', '/']):
                return None
            
            result = eval(clean)
            
            return {
                "type": "math",
                "title": "Калькулятор",
                "content": f"{clean.strip()} = {result}",
                "action": "Вычислить ещё"
            }
        except:
            return None
    
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
                "title": "Курс валют",
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
                    "title": "Курсы валют",
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
                "title": "Конвертер валют",
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
                "title": f"Погода в {weather_data.get('city', city)}",
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
                    "title": f"Найдено в новостях ({len(matching)})",
                    "content": preview,
                    "action": "Открыть новости"
                }
            
            return None
        except:
            return None
    
    def _search_wikipedia(self, query: str) -> Optional[Dict]:
        """Поиск в Wikipedia"""
        driver = self._get_driver()
        if not driver:
            return None
        
        try:
            # Формируем поисковый URL
            search_term = query.replace(' ', '+')
            if 'что такое' in query.lower():
                search_term = query.lower().replace('что такое', '').strip().replace(' ', '+')
            
            # Используем поиск Wikipedia
            url = f"https://ru.wikipedia.org/w/index.php?search={search_term}&title=Служебная:Поиск&profile=default&fulltext=1"
            
            driver.get(url)
            time.sleep(3)
            
            from selenium.webdriver.common.by import By
            
            # Проверяем, есть ли результаты поиска
            results = driver.find_elements(By.CSS_SELECTOR, "div.mw-search-result-heading a")
            
            if results:
                # Берем первый результат
                first_link = results[0].get_attribute('href')
                driver.get(first_link)
                time.sleep(2)
            
            # Получаем заголовок
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, "h1.firstHeading")
                title = title_elem.text.strip()
            except:
                title = query
            
            # Получаем содержимое
            try:
                # Ищем первый значимый параграф
                paragraphs = driver.find_elements(By.CSS_SELECTOR, "div.mw-parser-output > p")
                snippet = ""
                for p in paragraphs:
                    text = p.text.strip()
                    # Пропускаем пустые и короткие
                    if len(text) > 100 and not text.startswith("("):
                        snippet = text[:500]
                        if len(snippet) > 490:
                            snippet += "..."
                        break
                
                if not snippet:
                    return None
                    
            except:
                return None
            
            # Проверяем, что это не страница ошибки
            if "не существует" in title.lower() or "ошибка" in title.lower():
                return None
            
            return {
                "type": "wiki",
                "title": title,
                "content": snippet,
                "url": driver.current_url,
                "action": "Открыть статью"
            }
            
        except Exception as e:
            print(f"[Search] Ошибка Wikipedia: {e}")
            return None
    
    def _search_duckduckgo(self, query: str) -> List[Dict]:
        """Поиск в DuckDuckGo"""
        driver = self._get_driver()
        if not driver:
            return []
        
        results = []
        
        try:
            # Используем HTML-версию DuckDuckGo (без JS)
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            
            driver.get(search_url)
            time.sleep(3)
            
            from selenium.webdriver.common.by import By
            
            # Ищем результаты
            result_elements = driver.find_elements(By.CSS_SELECTOR, "div.result")
            
            for elem in result_elements[:5]:
                try:
                    # Заголовок и ссылка
                    link_elem = elem.find_element(By.CSS_SELECTOR, "a.result__a")
                    title = link_elem.text.strip()
                    url = link_elem.get_attribute('href')
                    
                    # Пропускаем рекламу и пустые
                    if not title or "реклама" in title.lower():
                        continue
                    
                    # Описание
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
                    print(f"[Search] Ошибка парсинга результата: {e}")
                    continue
            
            # Если мало результатов, пробуем обычную версию
            if len(results) < 2:
                print("[Search] Мало результатов, пробуем основной DDG...")
                
                search_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
                driver.get(search_url)
                time.sleep(4)
                
                try:
                    # Ждем загрузки
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    
                    wait = WebDriverWait(driver, 10)
                    
                    # Пробуем разные селекторы
                    selectors = [
                        "[data-testid='result']",
                        ".result",
                        "article",
                    ]
                    
                    result_elements = []
                    for selector in selectors:
                        try:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            result_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if result_elements:
                                break
                        except:
                            continue
                    
                    for elem in result_elements[:5]:
                        try:
                            # Пробуем разные селекторы для заголовка
                            title_selectors = [
                                "[data-testid='result-title-a']",
                                "h2 a",
                                "a[href]"
                            ]
                            
                            title = url = ""
                            for sel in title_selectors:
                                try:
                                    title_elem = elem.find_element(By.CSS_SELECTOR, sel)
                                    title = title_elem.text.strip()
                                    url = title_elem.get_attribute('href')
                                    if title and url:
                                        break
                                except:
                                    continue
                            
                            if not title or not url:
                                continue
                            
                            # Описание
                            snippet = "Нет описания"
                            snippet_selectors = [
                                "[data-testid='result-snippet']",
                                ".result__snippet",
                                "p"
                            ]
                            
                            for sel in snippet_selectors:
                                try:
                                    snippet_elem = elem.find_element(By.CSS_SELECTOR, sel)
                                    snippet = snippet_elem.text.strip()[:200]
                                    if len(snippet) > 190:
                                        snippet += "..."
                                    if len(snippet) > 20:
                                        break
                                except:
                                    continue
                            
                            results.append({
                                "type": "web",
                                "title": title,
                                "content": snippet,
                                "url": url,
                                "action": "Открыть"
                            })
                            
                        except Exception as e:
                            print(f"[Search] Ошибка парсинга: {e}")
                            continue
                            
                except Exception as e:
                    print(f"[Search] Ошибка основного DDG: {e}")
        
        except Exception as e:
            print(f"[Search] Ошибка веб-поиска: {e}")
        
        print(f"[Search] Найдено {len(results)} веб-результатов")
        return results
    
    def _query_gemini(self, query: str, context: Optional[str] = None) -> Optional[Dict]:
        """Запрос к Google Gemini для произвольных вопросов"""
        try:
            import config
            if not config.GEMINI_API_KEY:
                print("[Search] GEMINI_API_KEY не найден")
                return None
            
            genai.configure(api_key=config.GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Если есть контекст, это уточнение
            if context:
                prompt = f"Коротко я ответил на вопрос:\n\"{context}\"\n\nТеперь пользователь уточняет: \"{query}\"\n\nОтвети на уточнение на русском языке, как продолжение предыдущего ответа. Будь полезным и информативным."
            else:
                prompt = f"Ответь кратко и точно на русском языке на вопрос: {query}. Будь полезным и информативным."
            
            response = model.generate_content(prompt)
            
            if response and response.text:
                answer = response.text.strip()
                return {
                    "type": "ai",
                    "title": "🤖 ИИ-ответ",
                    "content": answer,
                    "action": "Задать уточнение"
                }
        except Exception as e:
            print(f"[Search] Ошибка Gemini: {e}")
            return None
        return None
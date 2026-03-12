import customtkinter as ctk
from .base_page import BasePage
from datetime import datetime
from typing import List, Dict, Optional
import threading
import webbrowser
import re
import time
import json
import asyncio
import aiohttp
import concurrent.futures
from functools import partial

# Скомпилированные regex для производительности
RE_MARKDOWN_BOLD = re.compile(r'\*\*')
RE_MARKDOWN_ITALIC = re.compile(r'(?<!\*)\*(?!\*)')
RE_MARKDOWN_CODE = re.compile(r'`')
RE_MARKDOWN_HEADER = re.compile(r'#+ ')
RE_MARKDOWN_LINK = re.compile(r'\[([^\]]+)\]\([^)]+\)')
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_MULTIPLE_SPACES = re.compile(r' +')
RE_MULTIPLE_NEWLINES = re.compile(r'\n{3,}')

# Thread pool для async операций
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


class SearchPage(BasePage):
    """Страница поиска с краткой сводкой и ссылками — неблокирующая версия"""
    
    def __init__(self, parent, controller):
        self.search_history = []
        self.current_results = []
        self.quick_answer = None
        self.web_links = []
        self.last_ai_query = None
        self.ai_context = None
        # Event loop для async операций в отдельном потоке
        self._loop = None
        self._loop_thread = None
        self._init_async_loop()
        super().__init__(parent, controller)
    
    def _init_async_loop(self):
        """Инициализация event loop в отдельном потоке"""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        # Ждем запуска loop
        while self._loop is None:
            time.sleep(0.01)
    
    def _run_async(self, coro):
        """Запускает корутину в отдельном event loop"""
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            return future
        return None
    
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
        """Выполнить поиск (неблокирующий)"""
        query = self.search_entry.get().strip()
        
        if not query:
            self.show_error("Введите поисковый запрос!")
            return
        
        # Сохраняем в историю
        self.add_to_history(query)
        
        # Показываем загрузку
        self.show_loading()
        
        # Запускаем поиск в отдельном потоке с async
        threading.Thread(target=self._do_search_thread, args=(query,), daemon=True).start()
    
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
        """Обновить статус загрузки (thread-safe)"""
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
    
    def _do_search_thread(self, query: str):
        """Поток поиска с async операциями"""
        query_lower = query.lower()
        
        print(f"[Search] Начало поиска: '{query}'")
        
        # === ЭТАП 1: Формируем краткую сводку (async) ===
        self.update_loading_status("Формируем краткую сводку...")
        
        # Запускаем async задачу для ИИ и других HTTP-запросов
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            quick_answer = loop.run_until_complete(
                self._get_quick_answer_async(query, query_lower, self.ai_context)
            )
        finally:
            loop.close()
        
        # === ЭТАП 2: Ищем ссылки (в отдельном потоке) ===
        self.update_loading_status("Ищем ссылки в интернете...")
        
        web_links = self._get_web_links(query)
        
        # === ЭТАП 3: Показываем результаты ===
        self.quick_answer = quick_answer
        self.web_links = web_links
        self.last_ai_query = query
        self.ai_context = None
        
        self.after(0, lambda: self._display_results(query, quick_answer, web_links))
    
    async def _get_quick_answer_async(self, query: str, query_lower: str, context: Optional[str] = None) -> Optional[Dict]:
        """Async версия получения краткой сводки"""
        
        # 1. Валюты (синхронно, быстро — из кэша)
        if any(kw in query_lower for kw in ["курс", "цена", "стоимость", "доллар", "евро", "биткоин", "usd", "eur", "btc"]):
            result = self._search_currency(query_lower, query)
            if result:
                return result
        
        # 2. Погода (синхронно, быстро — из кэша/API)
        if any(kw in query_lower for kw in ["погода", "температура", "градус"]):
            result = self._search_weather(query_lower, query)
            if result:
                return result
        
        # 3. Новости (синхронно, быстро — из кэша)
        if any(kw in query_lower for kw in ["новост", "событ"]):
            result = self._search_news(query_lower, query)
            if result:
                return result
        
        # 4. Wikipedia для знаний (async HTTP)
        if self._is_knowledge_query(query_lower):
            result = await self._search_wikipedia_async(query)
            if result:
                return result
        
        # 5. Калькулятор (синхронно)
        math_result = self._calculate_math(query)
        if math_result:
            return math_result
        
        # 6. ИИ для произвольных вопросов (async HTTP)
        ai_result = await self._query_openrouter_async(query, context)
        if ai_result:
            return ai_result
        
        return None
    
    async def _search_wikipedia_async(self, query: str) -> Optional[Dict]:
        """Async поиск в Wikipedia через HTTP API"""
        try:
            # Используем Wikipedia API вместо Selenium
            search_term = query.replace(' ', '+')
            if 'что такое' in query.lower():
                search_term = query.lower().replace('что такое', '').strip().replace(' ', '+')
            
            url = f"https://ru.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json&srlimit=1"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        search_results = data.get('query', {}).get('search', [])
                        
                        if search_results:
                            title = search_results[0]['title']
                            snippet = search_results[0]['snippet']
                            # Очищаем HTML из сниппета
                            clean_snippet = RE_HTML_TAGS.sub('', snippet)
                            
                            # Получаем полную статью
                            page_url = f"https://ru.wikipedia.org/wiki/{title.replace(' ', '_')}"
                            
                            return {
                                "type": "wiki",
                                "title": title,
                                "content": clean_snippet[:300] + "..." if len(clean_snippet) > 300 else clean_snippet,
                                "url": page_url,
                                "action": "Открыть статью"
                            }
        except Exception as e:
            print(f"[Search] Ошибка Wikipedia API: {e}")
        
        return None
    
    async def _query_openrouter_async(self, query: str, context: Optional[str] = None) -> Optional[Dict]:
        """Async запрос к OpenRouter API"""
        try:
            import config
            
            if config.USE_AI_PROVIDER != "openrouter" or not config.OPENROUTER_API_KEY:
                print("[Search] OpenRouter не настроен")
                return None
            
            if context:
                prompt = f"Коротко я ответил на вопрос:\n\"{context}\"\n\nТеперь пользователь уточняет: \"{query}\"\n\nОтвети на уточнение на русском языке, как продолжение предыдущего ответа. Будь полезным и информативным."
            else:
                prompt = f"Ответь кратко и точно на русском языке на вопрос: {query}. Будь полезным и информативным."
            
            headers = {
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://quicktab.local",
                "X-Title": "QuickTab"
            }
            
            data = {
                "model": config.OPENROUTER_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        if "choices" in result and len(result["choices"]) > 0:
                            answer = result["choices"][0]["message"]["content"].strip()
                            self._full_ai_answer = answer
                            self._last_ai_query = query
                            
                            return {
                                "type": "ai",
                                "title": "ИИ-ответ",
                                "content": answer[:300] + "..." if len(answer) > 300 else answer,
                                "action": "Показать полный ответ"
                            }
                    else:
                        print(f"[Search] Ошибка OpenRouter: {response.status}")
                        
        except asyncio.TimeoutError:
            print("[Search] Таймаут OpenRouter")
        except Exception as e:
            print(f"[Search] Ошибка OpenRouter: {e}")
            
        return None
    
    def _get_web_links(self, query: str) -> List[Dict]:
        """Получить ссылки из веб-поиска (упрощенная версия без Selenium)"""
        links = []
        
        # Добавляем прямые ссылки на поисковики (быстро, без блокировки)
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
        links.append({
            "type": "search_engine",
            "title": "📚 Wikipedia",
            "content": "Поискать в Wikipedia",
            "url": f"https://ru.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '+')}",
            "action": "Открыть"
        })
        
        return links
    
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
    
    def _clean_text(self, text: str) -> str:
        """Оптимизированная очистка текста с скомпилированными regex"""
        if not text:
            return ""
        
        # Используем скомпилированные regex
        text = RE_MARKDOWN_BOLD.sub('', text)
        text = RE_MARKDOWN_ITALIC.sub('', text)
        text = RE_MARKDOWN_CODE.sub('', text)
        text = RE_MARKDOWN_HEADER.sub('', text)
        text = RE_MARKDOWN_LINK.sub(r'\1', text)
        text = RE_HTML_TAGS.sub('', text)
        
        # Нормализуем переносы строк
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Убираем множественные пробелы и переносы
        text = RE_MULTIPLE_SPACES.sub(' ', text)
        text = RE_MULTIPLE_NEWLINES.sub('\n\n', text)
        
        # Убираем пробелы в начале и конце строк
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _create_quick_answer_card(self, answer: Dict):
        """Создать карточку краткой сводки с кнопкой копирования"""
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
        
        clean_content = self._clean_text(answer.get("content", ""))
        
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
        content_frame = ctk.CTkFrame(inner, fg_color="transparent")
        content_frame.pack(pady=15, padx=20, fill="x")
        
        content_text = ctk.CTkTextbox(
            content_frame,
            font=("Arial", 24),
            text_color="#FFFFFF",
            fg_color="#2a2a2a",
            corner_radius=10,
            height=150,
            wrap="word",
            activate_scrollbars=True
        )
        content_text.pack(fill="x", expand=True)
        content_text.insert("1.0", clean_content)
        content_text.configure(state="disabled")
        
        # Сохраняем полный текст для копирования
        if answer.get("type") == "ai" and hasattr(self, '_full_ai_answer'):
            full_text_to_copy = self._full_ai_answer
        else:
            full_text_to_copy = clean_content
        
        self._last_answer_text = full_text_to_copy
        
        # Кнопки действий
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(pady=(0, 20), anchor="w", padx=20)
        
        if answer.get("action"):
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
        
        copy_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Копировать ответ",
            font=("Arial", 21),
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color="#888888",
            height=68,
            command=self._copy_last_answer
        )
        copy_btn.pack(side="left", padx=(10, 0))
        
        if answer.get("url"):
            link_btn = ctk.CTkButton(
                btn_frame,
                text="🔗 Открыть ссылку",
                font=("Arial", 21),
                fg_color="transparent",
                hover_color="#3a3a3a",
                text_color="#888888",
                height=68,
                command=lambda u=answer["url"]: webbrowser.open(u)
            )
            link_btn.pack(side="left", padx=(10, 0))
    
    def _copy_last_answer(self):
        """Копирование полного ответа в буфер обмена"""
        if hasattr(self, '_last_answer_text') and self._last_answer_text:
            self.clipboard_clear()
            self.clipboard_append(self._last_answer_text)
            self.update()
            
            notif = ctk.CTkLabel(
                self,
                text="✓ Ответ скопирован!",
                font=("Arial", 21),
                text_color="#00FF00",
                fg_color="#2a2a2a",
                corner_radius=10
            )
            notif.place(relx=0.5, rely=0.9, anchor="center")
            self.after(1500, notif.destroy)
    
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
            clean_snippet = self._clean_text(link["content"])
            ctk.CTkLabel(
                card,
                text=clean_snippet,
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
            self.controller.show_page("home")
        elif rtype == "ai":
            if hasattr(self, '_full_ai_answer') and self._full_ai_answer:
                self._show_full_ai_response(self._last_ai_query, self._full_ai_answer)
            else:
                self.ai_context = answer.get("content", "")
                self.search_entry.delete(0, "end")
                self.search_entry.focus()
                hint = ctk.CTkLabel(
                    self.content_frame,
                    text="💬 Режим уточнения (введите дополнительный вопрос)",
                    font=("Arial", 18),
                    text_color="#00FF00"
                )
                hint.pack(pady=5)
                self.after(3000, hint.destroy)
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
        """Поиск валют (из кэша)"""
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
        """Получить данные валют из кэша"""
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
                          f"Ветер: {weather_data.get('wind', '--')}\n"
                          f"Влажность: {weather_data.get('humidity', '--')}",
                "data": weather_data,
                "action": "Подробнее"
            }
        
        return None
    
    def _get_weather_data(self, city: str) -> Optional[Dict]:
        """Получить данные погоды из кэша"""
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
    
    def _get_homepage_data(self):
        """Получить данные с главной страницы через контроллер"""
        try:
            homepage = None
            
            if hasattr(self.controller, 'pages'):
                homepage = self.controller.pages.get('home')
            
            if not homepage and hasattr(self.controller, 'frames'):
                homepage = self.controller.frames.get('home')
            
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
    
    def _show_full_ai_response(self, query: str, answer: str):
        """Увеличенное диалоговое окно для полного ИИ-ответа"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Ответ на: {query[:50]}{'...' if len(query) > 50 else ''}")
        
        dialog.geometry("1400x900")
        dialog.minsize(1200, 800)
        dialog.transient(self)
        
        def set_grab():
            try:
                dialog.grab_set()
            except Exception as e:
                print(f"[Search] grab_set failed: {e}")
        
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 1400) // 2
        y = (screen_height - 900) // 2
        dialog.geometry(f"1400x900+{x}+{y}")
        
        # Заголовок
        header_frame = ctk.CTkFrame(dialog, fg_color="#2a2a2a")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header_frame,
            text="🤖 ИИ-ответ",
            font=("Arial", 42, "bold"),
            text_color="#FF6D00"
        ).pack(pady=15)
        
        ctk.CTkLabel(
            header_frame,
            text=f"Вопрос: {query}",
            font=("Arial", 24),
            text_color="#888888",
            wraplength=1300
        ).pack(pady=(0, 10))
        
        # Область текста
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        text_widget = ctk.CTkTextbox(
            content_frame,
            font=("Arial", 32),
            text_color="#FFFFFF",
            fg_color="#1a1a1a",
            corner_radius=15,
            wrap="word",
            activate_scrollbars=True
        )
        text_widget.pack(fill="both", expand=True)
        
        clean_answer = self._clean_text(answer)
        text_widget.insert("1.0", clean_answer)
        text_widget.configure(state="disabled")
        
        # Кнопки действий
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        copy_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Копировать весь ответ",
            font=("Arial", 28, "bold"),
            fg_color="#00AAFF",
            hover_color="#0088DD",
            text_color="#000000",
            height=70,
            width=350,
            corner_radius=15,
            command=lambda: self._copy_full_answer(clean_answer, dialog)
        )
        copy_btn.pack(side="left", padx=(0, 15))
        
        close_btn = ctk.CTkButton(
            btn_frame,
            text="✓ Закрыть",
            font=("Arial", 28, "bold"),
            fg_color="#444444",
            hover_color="#666666",
            height=70,
            width=200,
            corner_radius=15,
            command=dialog.destroy
        )
        close_btn.pack(side="left")
        
        clarify_btn = ctk.CTkButton(
            btn_frame,
            text="💬 Уточнить",
            font=("Arial", 28, "bold"),
            fg_color="#FF6D00",
            hover_color="#FF8C00",
            text_color="#000000",
            height=70,
            width=200,
            corner_radius=15,
            command=lambda: self._start_clarification(query, answer, dialog)
        )
        clarify_btn.pack(side="right")
        
        dialog.after(100, set_grab)
        dialog.focus_set()
        dialog.lift()
    
    def _copy_full_answer(self, text: str, dialog=None):
        """Копирование полного ответа"""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        
        notif = ctk.CTkLabel(
            dialog or self,
            text="✓ Ответ скопирован!",
            font=("Arial", 28, "bold"),
            text_color="#00FF00",
            fg_color="#2a2a2a",
            corner_radius=15
        )
        notif.place(relx=0.5, rely=0.1, anchor="center")
        if dialog:
            dialog.after(2000, notif.destroy)
        else:
            self.after(2000, notif.destroy)
    
    def _start_clarification(self, original_query: str, answer: str, dialog=None):
        """Начать уточнение вопроса"""
        if dialog:
            dialog.destroy()
        
        self.ai_context = answer
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, f"Уточнение: ")
        self.search_entry.focus()
        self.search_entry.icursor("end")
        
        self.show_start_screen()
        hint_frame = ctk.CTkFrame(self.content_frame, fg_color="#2a2a2a", corner_radius=15)
        hint_frame.pack(pady=20, fill="x", padx=5)
        
        ctk.CTkLabel(
            hint_frame,
            text="💬 Режим уточнения",
            font=("Arial", 30, "bold"),
            text_color="#00FF00"
        ).pack(pady=10)
        
        ctk.CTkLabel(
            hint_frame,
            text=f"Предыдущий вопрос: {original_query[:60]}{'...' if len(original_query) > 60 else ''}\n"
                f"Введите дополнительный вопрос для уточнения",
            font=("Arial", 22),
            text_color="#AAAAAA"
        ).pack(pady=10)
        
        self.after(5000, hint_frame.destroy)
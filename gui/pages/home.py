import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import List, Dict, Optional
import threading
import concurrent.futures
from .base_page import BasePage

# Глобальные переменные для модулей (ленивый импорт)
_weather_module = None
_currency_module = None
_news_module = None
_import_lock = threading.Lock()

def _get_weather_module():
    global _weather_module
    with _import_lock:
        if _weather_module is None:
            from modules.weather import get_weather_data
            _weather_module = get_weather_data
    return _weather_module

def _get_currency_module():
    global _currency_module
    with _import_lock:
        if _currency_module is None:
            from modules.currency import get_currency_data
            _currency_module = get_currency_data
    return _currency_module

def _get_news_module():
    global _news_module
    with _import_lock:
        if _news_module is None:
            from modules.news import get_news_data
            _news_module = get_news_data
    return _news_module


class HomePage(BasePage):
    """
    Главная страница с МГНОВЕННЫМ отображением данных
    """
    
    def __init__(self, parent, controller):
        # Кэш для всех данных
        self.cache = {
            "weather": {"data": None, "city": "Белореченск"},
            "currency": {"data": None},
            "news": {
                "cyber": {"data": []},
                "politics": {"data": []},
                "economy": {"data": []},
                "tech": {"data": []}
            }
        }
        self.request_count = 0
        self.current_news_topic = "cyber"
        self.is_loading = False
        
        super().__init__(parent, controller)
        
        # Мгновенная загрузка данных
        self.after(10, self._load_data_async)
    
    def create_widgets(self):
        """Создает интерфейс с увеличенными шрифтами"""
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._create_header()
        self._create_weather_widget()
        self._create_currency_cards()
        self._create_news_feed()
        self._create_history_section()
        self._create_fab_button()
    
    def _create_header(self):
        """Шапка"""
        header = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        hour = datetime.now().hour
        greeting = "Доброе утро" if 5 <= hour < 12 else \
                   "Добрый день" if 12 <= hour < 18 else \
                   "Добрый вечер" if 18 <= hour < 23 else "Доброй ночи"
        
        self.greeting_label = ctk.CTkLabel(
            header,
            text=f"{greeting}! 👋",
            font=("Arial", 36, "bold"),
            text_color="#FFFFFF"
        )
        self.greeting_label.pack(anchor="w")
        
        date_str = datetime.now().strftime("%d %B %Y, %A")
        self.date_label = ctk.CTkLabel(
            header,
            text=date_str,
            font=("Arial", 20),
            text_color="#888888"
        )
        self.date_label.pack(anchor="w", pady=(5, 0))
    
    def _create_weather_widget(self):
        """Виджет погоды"""
        self.weather_frame = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="#1E3A5F",
            corner_radius=20,
            height=200
        )
        self.weather_frame.pack(fill="x", pady=10)
        self.weather_frame.pack_propagate(False)
        
        inner = ctk.CTkFrame(self.weather_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Левая часть
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")
        
        self.weather_icon = ctk.CTkLabel(left, text="🌤️", font=("Arial", 56))
        self.weather_icon.pack(anchor="w")
        
        self.weather_temp = ctk.CTkLabel(
            left, text="Загрузка...", font=("Arial", 52, "bold"), text_color="white"
        )
        self.weather_temp.pack(anchor="w")
        
        self.weather_desc = ctk.CTkLabel(
            left, text="Получение данных...", font=("Arial", 22), text_color="#B0D4F1"
        )
        self.weather_desc.pack(anchor="w")
        
        # Правая часть
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right", fill="y")
        
        self.weather_wind = ctk.CTkLabel(
            right, text="💨 Ветер: -- м/с", font=("Arial", 18), 
            text_color="#88AACC", anchor="e"
        )
        self.weather_wind.pack(anchor="e", pady=3)
        
        self.weather_humidity = ctk.CTkLabel(
            right, text="💧 Влажность: --%", font=("Arial", 18),
            text_color="#88AACC", anchor="e"
        )
        self.weather_humidity.pack(anchor="e", pady=3)
        
        self.weather_city = ctk.CTkLabel(
            right, text="📍 Город: Белореченск", font=("Arial", 18),
            text_color="#88AACC", anchor="e"
        )
        self.weather_city.pack(anchor="e", pady=3)
        
        # Кнопки
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        self.weather_refresh_btn = ctk.CTkButton(
            btn_frame, text="🔄 Обновить", command=self._refresh_weather,
            fg_color="white", text_color="#1E3A5F", hover_color="#DDDDDD",
            width=140, height=40, corner_radius=20, font=("Arial", 16, "bold")
        )
        self.weather_refresh_btn.pack(side="left", padx=(0, 10))
        
        self.weather_city_btn = ctk.CTkButton(
            btn_frame, text="📍 Сменить город", command=self._change_city,
            fg_color="transparent", border_width=1, border_color="white",
            text_color="white", hover_color="#334466",
            width=160, height=40, corner_radius=20, font=("Arial", 16)
        )
        self.weather_city_btn.pack(side="left")
    
    def _create_currency_cards(self):
        """Карточки валют"""
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", pady=10)
        container.grid_columnconfigure((0, 1, 2), weight=1)
        
        currencies = [("USD", "🇺🇸", "#00C853"), ("EUR", "🇪🇺", "#2979FF"), ("BTC", "₿", "#FF9100")]
        self.currency_cards = {}
        
        for i, (code, flag, color) in enumerate(currencies):
            card = ctk.CTkFrame(
                container, fg_color="#2A2A2A", corner_radius=15,
                border_width=1, border_color="#3A3A3A"
            )
            card.grid(row=0, column=i, padx=10, pady=5, sticky="nsew")
            
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=20, pady=(20, 5))
            
            ctk.CTkLabel(header, text=flag, font=("Arial", 32)).pack(side="left")
            ctk.CTkLabel(header, text=code, font=("Arial", 26, "bold"), 
                        text_color=color).pack(side="left", padx=(15, 0))
            
            rate_label = ctk.CTkLabel(
                card, text="Загрузка...", font=("Courier", 36, "bold"), text_color="white"
            )
            rate_label.pack(pady=15)
            
            change_label = ctk.CTkLabel(
                card, text="ЦБ РФ", font=("Arial", 16), text_color="#666666"
            )
            change_label.pack()
            
            self.currency_cards[code] = {"rate": rate_label, "change": change_label}
    
    def _create_news_feed(self):
        """Лента новостей"""
        news_container = ctk.CTkFrame(
            self.scroll_frame, fg_color="#2A2A2A", corner_radius=20
        )
        news_container.pack(fill="x", pady=10, ipady=15)
        
        # Заголовок
        header = ctk.CTkFrame(news_container, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(header, text="📰 Лента новостей",
                    font=("Arial", 40, "bold"),
                    text_color="white").pack(side="left")
        
        # Переключатель категорий
        self.news_topic_var = ctk.StringVar(value="cyber")
        topics = [
            ("🛡️", "cyber", "Кибербезопасность"),
            ("🌍", "politics", "Политика"),
            ("💰", "economy", "Экономика"),
            ("🚀", "tech", "Технологии"),
        ]
        
        topic_frame = ctk.CTkFrame(header, fg_color="transparent")
        topic_frame.pack(side="right")
        
        for emoji, value, label in topics:
            btn = ctk.CTkButton(
                topic_frame,
                text=f"{emoji} {label}",
                command=lambda v=value: self._switch_news_topic(v),
                fg_color="#00AAFF" if value == "cyber" else "transparent",
                text_color="white" if value == "cyber" else "#888888",
                hover_color="#0066AA",
                width=200,
                height=50,
                corner_radius=25,
                font=("Arial", 20)
            )
            btn.pack(side="left", padx=5)
            setattr(self, f"news_btn_{value}", btn)
        
        # Список новостей
        self.news_list = ctk.CTkFrame(news_container, fg_color="transparent")
        self.news_list.pack(fill="x", padx=25, pady=15)
        
        self.news_items_widgets = []
        for i in range(5):
            widget = self._create_news_item_big(i)
            self.news_items_widgets.append(widget)
    
    def _create_news_item_big(self, index: int):
        """Элемент новости"""
        item = ctk.CTkFrame(self.news_list, fg_color="transparent", height=80)
        item.pack(fill="x", pady=5)
        item.pack_propagate(False)
        
        indicator = ctk.CTkFrame(item, fg_color="gray", width=6, corner_radius=3)
        indicator.pack(side="left", fill="y", padx=(0, 20))
        
        text_frame = ctk.CTkFrame(item, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        
        title_label = ctk.CTkLabel(
            text_frame,
            text="Загрузка...",
            font=("Arial", 25),
            text_color="white",
            anchor="w",
            wraplength=800
        )
        title_label.pack(fill="x", pady=(10, 5))
        
        time_label = ctk.CTkLabel(
            text_frame,
            text="",
            font=("Arial", 24),
            text_color="#666666",
            anchor="w"
        )
        time_label.pack(fill="x")
        
        open_btn = ctk.CTkButton(
            item, text="→", width=50, height=50,
            corner_radius=25,
            fg_color="transparent", hover_color="#3A3A3A",
            text_color="#888888", font=("Arial", 28),
            command=lambda idx=index: self._open_news(idx)
        )
        open_btn.pack(side="right", padx=10)
        
        return {
            "frame": item,
            "title": title_label,
            "time": time_label,
            "indicator": indicator,
            "url": None
        }
    
    def _create_history_section(self):
        """История запросов"""
        hist_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        hist_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(hist_frame, text="📊 История запросов",
                    font=("Arial", 28, "bold"), text_color="white").pack(anchor="w")
        
        self.history_list = ctk.CTkFrame(hist_frame, fg_color="#2A2A2A", corner_radius=15)
        self.history_list.pack(fill="x", pady=10)
        
        self.history_items = []
        for i in range(5):
            item = ctk.CTkFrame(self.history_list, fg_color="transparent", height=60)
            item.pack(fill="x", padx=15, pady=5)
            item.pack_propagate(False)
            
            ctk.CTkLabel(item, text=f"#{i+1}", font=("Courier", 18),
                        text_color="#888888").pack(side="left")
            
            time_label = ctk.CTkLabel(item, text="", font=("Courier", 16),
                        text_color="#666666")
            time_label.pack(side="left", padx=(15, 0))
            
            desc_label = ctk.CTkLabel(item, text="", font=("Arial", 16),
                        text_color="white")
            desc_label.pack(side="left", padx=15)
            
            self.history_items.append({"time": time_label, "desc": desc_label})
    
    def _create_fab_button(self):
        """Плавающая кнопка"""
        self.fab = ctk.CTkButton(
            self, text="🚀 Обновить всё", command=self._refresh_all,
            fg_color="#00AAFF", hover_color="#0088DD",
            width=180, height=55, corner_radius=27,
            font=("Arial", 18, "bold")
        )
        self.fab.place(relx=0.98, rely=0.98, anchor="se")
    
    # === Загрузка данных ===
    
    def _load_data_async(self):
        """Асинхронная загрузка всех данных"""
        self.controller.update_status("Загрузка...", "#FFFF00")
        
        def load_all():
            # Параллельная загрузка всех данных
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(self._fetch_weather): "weather",
                    executor.submit(self._fetch_currency): "currency",
                }
                
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        if task == "weather" and result:
                            self.after(0, lambda: self._update_weather_ui(result))
                        elif task == "currency" and result:
                            self.after(0, lambda: self._update_currency_ui(result))
                    except Exception as e:
                        print(f"Ошибка загрузки {task}: {e}")
            
            self.after(0, lambda: self.controller.update_status("Готово", "#00FF00"))
        
        threading.Thread(target=load_all, daemon=True).start()
    
    def _fetch_weather(self) -> Optional[Dict]:
        """Получение погоды через API"""
        try:
            get_weather_data = _get_weather_module()
            data = get_weather_data(None, self.cache["weather"]["city"])
            self.cache["weather"]["data"] = data
            print(f"[Weather] Получено: {data.get('temp', 'N/A')}")
            return data
        except Exception as e:
            print(f"[Weather] Ошибка: {e}")
            return None
    
    def _fetch_currency(self) -> Optional[Dict]:
        """Получение валют"""
        try:
            get_currency_data = _get_currency_module()
            driver = getattr(self.controller, 'driver', None)
            data = get_currency_data(driver)
            self.cache["currency"]["data"] = data
            print(f"[Currency] Получено: {data}")
            return data
        except Exception as e:
            print(f"[Currency] Ошибка: {e}")
            return None
    
    def _fetch_news(self, topic: str) -> Optional[Dict]:
        """Получение новостей"""
        try:
            get_news_data = _get_news_module()
            driver = getattr(self.controller, 'driver', None)
            items = get_news_data(driver, topic)
            self.cache["news"][topic]["data"] = items
            print(f"[News {topic}] Получено: {len(items)} новостей")
            return {"topic": topic, "items": items}
        except Exception as e:
            print(f"[News {topic}] Ошибка: {e}")
            return None
    
    # === Обновление UI ===
    
    def _update_weather_ui(self, data: dict):
        """Обновить погоду"""
        print(f"[UI] Обновление погоды: {data}")
        self.weather_temp.configure(text=data.get("temp", "--°C"))
        self.weather_desc.configure(text=data.get("desc", "Нет данных"))
        self.weather_wind.configure(text=f"💨 Ветер: {data.get('wind', '-- м/с')}")
        self.weather_humidity.configure(text=f"💧 Влажность: {data.get('humidity', '--%')}")
        self.weather_city.configure(text=f"📍 Город: {data.get('city', 'Белореченск')}")
        
        # Иконка по погоде
        desc = data.get("desc", "").lower()
        icon = "🌤️"
        if "дождь" in desc or "морось" in desc: icon = "🌧️"
        elif "снег" in desc: icon = "❄️"
        elif "ясно" in desc or "солнечно" in desc: icon = "☀️"
        elif "облачно" in desc or "пасмурно" in desc: icon = "☁️"
        elif "туман" in desc: icon = "🌫️"
        self.weather_icon.configure(text=icon)
    
    def _update_currency_ui(self, data: dict):
        """Обновить валюты"""
        print(f"[UI] Обновление валют: {data}")
        for code, rate in data.items():
            if code in self.currency_cards:
                self.currency_cards[code]["rate"].configure(text=rate)
    
    def _update_news_ui(self, items: list, topic: str):
        """Обновить новости"""
        print(f"[UI] Обновление новостей {topic}: {len(items)} шт")
        colors = {"cyber": "#FF5252", "politics": "#448AFF", 
                 "economy": "#00C853", "tech": "#FF9100"}
        color = colors.get(topic, "gray")
        
        # Очищаем
        for widget in self.news_items_widgets:
            widget["title"].configure(text="")
            widget["time"].configure(text="")
            widget["indicator"].configure(fg_color="gray")
            widget["url"] = None
        
        # Заполняем
        for i, item in enumerate(items[:5]):
            if i < len(self.news_items_widgets):
                widget = self.news_items_widgets[i]
                title = item.get("title", "")
                widget["title"].configure(text=title)
                widget["time"].configure(text="Только что")
                widget["indicator"].configure(fg_color=color)
                widget["url"] = item.get("url", item.get("summary", ""))
    
    # === Действия ===
    
    def _switch_news_topic(self, topic: str):
        """Переключение вкладки из кэша"""
        self.current_news_topic = topic
        self.news_topic_var.set(topic)
        
        # Обновляем стили кнопок
        for t in ["cyber", "politics", "economy", "tech"]:
            btn = getattr(self, f"news_btn_{t}", None)
            if btn:
                if t == topic:
                    btn.configure(fg_color="#00AAFF", text_color="white")
                else:
                    btn.configure(fg_color="transparent", text_color="#888888")
        
        # Показываем из кэша
        cached = self.cache["news"][topic]["data"]
        if cached:
            self._update_news_ui(cached, topic)
            self.controller.update_status(f"Новости: {topic}", "#00FF00")
        else:
            threading.Thread(target=lambda: self._load_news_for_topic(topic), daemon=True).start()
    
    def _load_news_for_topic(self, topic: str):
        """Загрузка новостей для вкладки"""
        result = self._fetch_news(topic)
        if result and result["items"]:
            self.after(0, lambda: self._update_news_ui(result["items"], topic))
    
    def _refresh_weather(self):
        """Обновить погоду"""
        threading.Thread(target=self._load_data_async, daemon=True).start()
    
    def _refresh_all(self):
        """Обновить всё"""
        self.request_count += 1
        now = datetime.now().strftime("%H:%M")
        
        # История
        for i in range(len(self.history_items) - 1, 0, -1):
            self.history_items[i]["time"].configure(
                text=self.history_items[i-1]["time"].cget("text"))
            self.history_items[i]["desc"].configure(
                text=self.history_items[i-1]["desc"].cget("text"))
        
        self.history_items[0]["time"].configure(text=now)
        self.history_items[0]["desc"].configure(
            text=f"#{self.request_count}  Погода + Валюты + Новости")
        
        self._load_data_async()
        
        # Загружаем новости для всех тем параллельно
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._fetch_news, "cyber"): "cyber",
                executor.submit(self._fetch_news, "politics"): "politics",
                executor.submit(self._fetch_news, "economy"): "economy",
                executor.submit(self._fetch_news, "tech"): "tech",
            }
            
            for future in concurrent.futures.as_completed(futures):
                topic = futures[future]
                try:
                    result = future.result()
                    if result and topic == self.current_news_topic:
                        self.after(0, lambda r=result, t=topic: self._update_news_ui(r["items"], t))
                except Exception as e:
                    print(f"Ошибка загрузки новостей {topic}: {e}")
    
    def _change_city(self):
        """Сменить город"""
        dialog = ctk.CTkInputDialog(text="Введите город:", title="Смена города", width=600, height=300)
        city = dialog.get_input()
        if city:
            self.cache["weather"]["city"] = city
            threading.Thread(target=self._load_data_async, daemon=True).start()
    
    def _open_news(self, index: int):
        """Открыть новость"""
        if index < len(self.news_items_widgets):
            url = self.news_items_widgets[index].get("url")
            if url and url.startswith("http"):
                import webbrowser
                webbrowser.open(url)
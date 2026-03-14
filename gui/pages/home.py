import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import List, Dict, Optional
import threading
import concurrent.futures
import json
import os
import webbrowser
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
        # ИСПРАВЛЕНО: используем threading.Lock для всех операций с драйвером
        self._driver_lock = threading.Lock()
        
        # Данные избранного
        self.favorites_data = []
        self.fav_cards = []
        
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
        self._create_favorites_section()
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
                card, text="--", font=("Courier", 36, "bold"), text_color="white"
            )
            rate_label.pack(pady=15)
            
            change_label = ctk.CTkLabel(
                card, text="ЦБ РФ", font=("Arial", 16), text_color="#666666"
            )
            change_label.pack()
            
            self.currency_cards[code] = {"rate": rate_label, "change": change_label}
    
    def _create_news_feed(self):
        """Лента новостей УМЕНЬШЕННАЯ в 1.5 раза"""
        news_container = ctk.CTkFrame(
            self.scroll_frame, fg_color="#2A2A2A", corner_radius=20
        )
        news_container.pack(fill="x", pady=10, ipady=15)
        
        # Заголовок
        header = ctk.CTkFrame(news_container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(header, text="📰 Лента новостей",
                    font=("Arial", 32, "bold"),
                    text_color="white").pack(side="left")
        
        # Переключатель категорий
        self.news_topic_var = ctk.StringVar(value="cyber")
        topics = [
            ("🛡️", "cyber", "Кибер"),
            ("🌍", "politics", "Политика"),
            ("💰", "economy", "Экономика"),
            ("🚀", "tech", "Техно"),
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
                width=225,
                height=35,
                corner_radius=39,
                font=("Arial", 32),
                anchor="center"
            )
            btn.pack(side="left", padx=3)
            setattr(self, f"news_btn_{value}", btn)
        
        # Список новостей — 5 элементов
        self.news_list = ctk.CTkFrame(news_container, fg_color="transparent")
        self.news_list.pack(fill="x", padx=20, pady=10)
        
        self.news_items_widgets = []
        for i in range(5):
            widget = self._create_news_item(i)
            self.news_items_widgets.append(widget)
    
    def _create_news_item(self, index: int):
        """Элемент новости УМЕНЬШЕННЫЙ"""
        item = ctk.CTkFrame(self.news_list, fg_color="transparent", height=80)
        item.pack(fill="x", pady=5)
        item.pack_propagate(False)
        
        indicator = ctk.CTkFrame(item, fg_color="gray", width=6, corner_radius=3)
        indicator.pack(side="left", fill="y", padx=(0, 15))
        
        text_frame = ctk.CTkFrame(item, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        
        title_label = ctk.CTkLabel(
            text_frame,
            text="Загрузка...",
            font=("Arial", 24),
            text_color="white",
            anchor="w",
            wraplength=800
        )
        title_label.pack(fill="x", pady=(10, 3))
        
        time_label = ctk.CTkLabel(
            text_frame,
            text="",
            font=("Arial", 18),
            text_color="#666666",
            anchor="w"
        )
        time_label.pack(fill="x")
        
        open_btn = ctk.CTkButton(
            item, text="→", width=50, height=50,
            corner_radius=25,
            fg_color="transparent", hover_color="#3A3A3A",
            text_color="#888888", font=("Arial", 24),
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
    
    def _create_favorites_section(self):
        """Избранное в виде красивых карточек с пользовательскими сайтами"""
        fav_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        fav_frame.pack(fill="x", pady=15)
        
        # Заголовок с кнопкой добавления
        header = ctk.CTkFrame(fav_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            header, 
            text="⭐ Избранное",
            font=("Arial", 28, "bold"), 
            text_color="white"
        ).pack(side="left")
        
        add_btn = ctk.CTkButton(
            header,
            text="+ Добавить сайт",
            command=self._show_add_favorite_dialog,
            fg_color="#00AAFF",
            hover_color="#0088DD",
            width=150,
            height=35,
            corner_radius=17,
            font=("Arial", 14, "bold")
        )
        add_btn.pack(side="right")
        
        # Сетка карточек (максимум 6 штук, 3 в ряд)
        self.fav_container = ctk.CTkFrame(fav_frame, fg_color="transparent")
        self.fav_container.pack(fill="x")
        self.fav_container.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Загружаем сохраненные избранные
        self._load_favorites()
        
        # Если пусто — создаем пустые слоты
        if not self.favorites_data:
            for i in range(6):
                self._create_empty_fav_slot(i)
    
    def _create_empty_fav_slot(self, index: int):
        """Создает пустой слот для избранного"""
        row = index // 3
        col = index % 3
        
        # Пустая карточка с приглашением
        card = ctk.CTkFrame(
            self.fav_container,
            fg_color="#2A2A2A",
            corner_radius=20,
            border_width=2,
            border_color="#3A3A3A",
            height=120
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.pack_propagate(False)
        
        # Приглашение добавить
        plus_label = ctk.CTkLabel(
            card,
            text="+",
            font=("Arial", 48),
            text_color="#555555"
        )
        plus_label.place(relx=0.5, rely=0.4, anchor="center")
        
        hint_label = ctk.CTkLabel(
            card,
            text="Добавить сайт",
            font=("Arial", 14),
            text_color="#666666"
        )
        hint_label.place(relx=0.5, rely=0.75, anchor="center")
        
        # Клик по карточке открывает диалог
        card.bind("<Button-1>", lambda e: self._show_add_favorite_dialog())
        plus_label.bind("<Button-1>", lambda e: self._show_add_favorite_dialog())
        hint_label.bind("<Button-1>", lambda e: self._show_add_favorite_dialog())
        
        # Hover эффект
        def on_enter(e):
            card.configure(border_color="#00AAFF", fg_color="#333333")
            plus_label.configure(text_color="#00AAFF")
        
        def on_leave(e):
            card.configure(border_color="#3A3A3A", fg_color="#2A2A2A")
            plus_label.configure(text_color="#555555")
        
        for widget in [card, plus_label, hint_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        self.fav_cards.append({
            "frame": card,
            "type": "empty",
            "index": index
        })
    
    def _create_fav_card(self, index: int, data: dict):
        """Создает заполненную карточку сайта с улучшенными кнопками"""
        row = index // 3
        col = index % 3
        
        # Удаляем старую карточку если есть
        if index < len(self.fav_cards):
            self.fav_cards[index]["frame"].destroy()
        
        # Цвета для категорий
        category_colors = {
            "social": "#FF6B6B",
            "news": "#4ECDC4",
            "video": "#FF6B9D",
            "work": "#45B7D1",
            "shop": "#96CEB4",
            "other": "#FECA57"
        }
        color = category_colors.get(data.get("category", "other"), "#FECA57")
        
        # Карточка с цветным акцентом
        card = ctk.CTkFrame(
            self.fav_container,
            fg_color="#2A2A2A",
            corner_radius=20,
            border_width=3,
            border_color=color,
            height=120
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.pack_propagate(False)
        
        # Внутренний контейнер
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=12)
        
        # ЛЕВАЯ ЧАСТЬ: Иконка и текст
        left_frame = ctk.CTkFrame(inner, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)
        
        # Иконка (emoji или первая буква)
        icon_text = data.get("icon", "")
        if not icon_text:
            icon_text = data.get("title", "S")[0].upper()
        
        icon_frame = ctk.CTkFrame(
            left_frame,
            fg_color=color,
            corner_radius=12,
            width=70,
            height=70
        )
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(
            icon_frame,
            text=icon_text,
            font=("Arial", 32),
            text_color="white"
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Текстовая часть
        text_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        title = ctk.CTkLabel(
            text_frame,
            text=data.get("title", "Без названия"),
            font=("Arial", 24, "bold"),
            text_color="white",
            anchor="w"
        )
        title.pack(fill="x")
        
        url_short = data.get("url", "").replace("https://", "").replace("http://", "")[:22]
        if len(url_short) > 22:
            url_short += "..."
        
        url_label = ctk.CTkLabel(
            text_frame,
            text=url_short,
            font=("Arial", 18),
            text_color="#888888",
            anchor="w"
        )
        url_label.pack(fill="x")
        
        # ПРАВАЯ ЧАСТЬ: Кнопки действий в ряд
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right", fill="y")
        
        # Стиль для всех кнопок
        btn_config = {
            "width": 50,
            "height": 50,
            "corner_radius": 18,
            "font": ("Arial", 16),
            "border_width": 0
        }
        
        # Кнопка открытия (самая заметная)
        open_btn = ctk.CTkButton(
            btn_frame,
            text="↗",
            fg_color=color,
            hover_color="#FFFFFF",
            text_color="#1A1A1A",
            **btn_config,
            command=lambda: self._open_favorite(index)
        )
        open_btn.pack(side="left", padx=2)
        
        # Кнопка редактирования
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✎",
            fg_color="#3A3A3A",
            hover_color="#FFA500",
            text_color="#CCCCCC",
            **btn_config,
            command=lambda: self._edit_favorite(index)
        )
        edit_btn.pack(side="left", padx=2)
        
        # Кнопка удаления
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="✕",
            fg_color="#3A3A3A",
            hover_color="#FF5252",
            text_color="#CCCCCC",
            **btn_config,
            command=lambda: self._remove_favorite(index)
        )
        delete_btn.pack(side="left", padx=2)
        
        # Hover эффекты для всей карточки
        def on_enter(e):
            card.configure(fg_color="#333333", border_width=4)
            # Подсвечиваем все кнопки
            edit_btn.configure(fg_color="#4A4A4A")
            delete_btn.configure(fg_color="#4A4A4A")
        
        def on_leave(e):
            card.configure(fg_color="#2A2A2A", border_width=3)
            # Возвращаем цвет кнопок
            edit_btn.configure(fg_color="#3A3A3A")
            delete_btn.configure(fg_color="#3A3A3A")
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        
        # Клик по основной части открывает сайт
        def on_click(e):
            # Проверяем, что клик не по кнопкам
            widget = e.widget
            # Если клик был по кнопке или её дочернему элементу - не открываем
            if "button" in str(widget).lower():
                return
            self._open_favorite(index)
        
        card.bind("<Button-1>", on_click)
        left_frame.bind("<Button-1>", on_click)
        text_frame.bind("<Button-1>", on_click)
        icon_frame.bind("<Button-1>", on_click)
        icon_label.bind("<Button-1>", on_click)
        title.bind("<Button-1>", on_click)
        url_label.bind("<Button-1>", on_click)
        
        # Сохраняем в список
        card_info = {
            "frame": card,
            "type": "filled",
            "data": data,
            "index": index
        }
        
        if index < len(self.fav_cards):
            self.fav_cards[index] = card_info
        else:
            while len(self.fav_cards) < index:
                self.fav_cards.append(None)
            self.fav_cards.append(card_info)
    
    def _show_add_favorite_dialog(self, edit_index: int = None):
        """Диалог добавления/редактирования избранного"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить сайт" if edit_index is None else "Редактировать сайт")
        dialog.geometry("1600x1100")
        dialog.transient(self)
        self.after(100, dialog.grab_set)
        
        # Заголовок
        ctk.CTkLabel(
            dialog,
            text="🌐 Добавить в избранное" if edit_index is None else "✎ Редактировать",
            font=("Arial", 36, "bold")
        ).pack(pady=40)
        
        # Поля ввода
        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="x", padx=60, pady=20)
        
        # Название
        ctk.CTkLabel(form_frame, text="Название:", font=("Arial", 24), anchor="w").pack(fill="x", pady=(20, 10))
        title_entry = ctk.CTkEntry(form_frame, height=70, font=("Arial", 24), placeholder_text="Например: YouTube")
        title_entry.pack(fill="x")
        
        # URL
        ctk.CTkLabel(form_frame, text="URL:", font=("Arial", 24), anchor="w").pack(fill="x", pady=(30, 10))
        url_entry = ctk.CTkEntry(form_frame, height=70, font=("Arial", 24), placeholder_text="https://...")
        url_entry.pack(fill="x")
        
        # Иконка (emoji) - НЕОБЯЗАТЕЛЬНОЕ ПОЛЕ
        ctk.CTkLabel(form_frame, text="Иконка (emoji) — необязательно:", font=("Arial", 24), anchor="w").pack(fill="x", pady=(30, 10))
        icon_entry = ctk.CTkEntry(form_frame, height=70, font=("Arial", 24), placeholder_text="Оставьте пустым для автоматической иконки")
        icon_entry.pack(fill="x")
        
        # Категория (цвет)
        ctk.CTkLabel(form_frame, text="Категория:", font=("Arial", 24), anchor="w").pack(fill="x", pady=(30, 15))
        
        category_var = ctk.StringVar(value="other")
        categories = [
            ("Соцсети", "social", "#FF6B6B"),
            ("Новости", "news", "#4ECDC4"),
            ("Видео", "video", "#FF6B9D"),
            ("Работа", "work", "#45B7D1"),
            ("Покупки", "shop", "#96CEB4"),
            ("Другое", "other", "#FECA57")
        ]
        
        cat_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        cat_frame.pack(fill="x", pady=10)
        
        for text, value, color in categories:
            rb = ctk.CTkRadioButton(
                cat_frame,
                text=text,
                variable=category_var,
                value=value,
                font=("Arial", 22),
                radiobutton_width=35,
                radiobutton_height=35,
                border_color=color,
                fg_color=color
            )
            rb.pack(anchor="w", pady=6)
        
        # Если редактирование — заполняем поля
        if edit_index is not None and edit_index < len(self.favorites_data):
            old_data = self.favorites_data[edit_index]
            title_entry.insert(0, old_data.get("title", ""))
            url_entry.insert(0, old_data.get("url", ""))
            icon_entry.insert(0, old_data.get("icon", ""))
            category_var.set(old_data.get("category", "other"))
        
        # Одна большая кнопка Готово
        def save():
            title = title_entry.get().strip()
            url = url_entry.get().strip()
            icon = icon_entry.get().strip()
            category = category_var.get()
            
            if not title or not url:
                messagebox.showerror("Ошибка", "Заполните название и URL!")
                return
            
            if not icon:
                icon = title[0].upper() if title else "🌐"
            
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            data = {
                "title": title,
                "url": url,
                "icon": icon,
                "category": category
            }
            
            if edit_index is not None:
                self.favorites_data[edit_index] = data
                self._create_fav_card(edit_index, data)
            else:
                added = False
                for i, card in enumerate(self.fav_cards):
                    if card["type"] == "empty":
                        self.favorites_data.append(data)
                        self._create_fav_card(i, data)
                        added = True
                        break
                
                if not added:
                    messagebox.showwarning("Место закончилось", "Максимум 6 избранных сайтов!")
                    return
            
            self._save_favorites()
            dialog.destroy()
        
        ctk.CTkButton(
            dialog,
            text="✓ Готово",
            command=save,
            fg_color="#00AAFF",
            hover_color="#0088DD",
            height=80,
            corner_radius=20,
            font=("Arial", 28, "bold")
        ).pack(fill="x", padx=60, pady=40)
    
    def _open_favorite(self, index: int):
        """Открыть сайт в браузере с активацией окна"""
        if index < len(self.fav_cards) and self.fav_cards[index]["type"] == "filled":
            url = self.fav_cards[index]["data"].get("url")
            if url:
                import subprocess
                import platform
                
                system = platform.system()
                try:
                    if system == "Linux":
                        subprocess.Popen(["xdg-open", url], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.DEVNULL)
                    elif system == "Darwin":  # macOS
                        subprocess.Popen(["open", url])
                    elif system == "Windows":
                        os.startfile(url)
                    else:
                        import webbrowser
                        webbrowser.open(url, new=2)
                    
                    self.controller.update_status(f"Открыт: {url}", "#00AAFF")
                except Exception as e:
                    print(f"Ошибка открытия браузера: {e}")
                    # Fallback
                    import webbrowser
                    webbrowser.open(url, new=2)
    
    def _edit_favorite(self, index: int):
        """Редактировать избранное"""
        self._show_add_favorite_dialog(edit_index=index)
    
    def _remove_favorite(self, index: int):
        """Удалить из избранного"""
        if messagebox.askyesno("Удалить", "Удалить этот сайт из избранного?"):
            # Удаляем из данных
            if index < len(self.favorites_data):
                self.favorites_data.pop(index)
            
            # Полностью пересоздаем сетку
            for card in self.fav_cards:
                card["frame"].destroy()
            self.fav_cards = []
            
            # Пересоздаем все карточки заново
            for i in range(6):
                if i < len(self.favorites_data):
                    self._create_fav_card(i, self.favorites_data[i])
                else:
                    self._create_empty_fav_slot(i)
            
            self._save_favorites()
            self.controller.update_status("Удалено из избранного", "#FF5252")
        
    def _save_favorites(self):
        """Сохранить избранное в файл"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".quicktab")
            os.makedirs(config_dir, exist_ok=True)  # ← создаём все родительские папки
            
            filepath = os.path.join(config_dir, "favorites.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.favorites_data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ Saved {len(self.favorites_data)} favorites to {filepath}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения избранного: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_favorites(self):
        """Загрузить избранное из файла"""
        try:
            # Очищаем старые карточки
            for card in self.fav_cards:
                if card and "frame" in card:
                    card["frame"].destroy()
            self.fav_cards = []
            
            config_path = os.path.join(os.path.expanduser("~"), ".quicktab", "favorites.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    self.favorites_data = json.load(f)
            else:
                self.favorites_data = []
            
            # Создаем все карточки заново
            for i in range(6):
                if i < len(self.favorites_data):
                    self._create_fav_card(i, self.favorites_data[i])
                else:
                    self._create_empty_fav_slot(i)
                    
        except Exception as e:
            print(f"Ошибка загрузки избранного: {e}")
            import traceback
            traceback.print_exc()
            self.favorites_data = []
            self.fav_cards = []
            for i in range(6):
                self._create_empty_fav_slot(i)
    
    def _create_history_section(self):
        """История запросов — 5 полей"""
        hist_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        hist_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(hist_frame, text="📊 История",
                    font=("Arial", 24, "bold"), text_color="white").pack(anchor="w")
        
        self.history_list = ctk.CTkFrame(hist_frame, fg_color="#2A2A2A", corner_radius=15)
        self.history_list.pack(fill="x", pady=10)
        
        self.history_items = []
        for i in range(5):
            item = ctk.CTkFrame(self.history_list, fg_color="transparent", height=50)
            item.pack(fill="x", padx=15, pady=4)
            item.pack_propagate(False)
            
            ctk.CTkLabel(item, text=f"#{i+1}", font=("Courier", 16),
                        text_color="#888888").pack(side="left")
            
            time_label = ctk.CTkLabel(item, text="", font=("Courier", 14),
                        text_color="#666666")
            time_label.pack(side="left", padx=(15, 0))
            
            desc_label = ctk.CTkLabel(item, text="", font=("Arial", 14),
                        text_color="white")
            desc_label.pack(side="left", padx=15)
            
            self.history_items.append({"time": time_label, "desc": desc_label})
    
    def _create_fab_button(self):
        """Плавающая кнопка"""
        self.fab = ctk.CTkButton(
            self, text="🚀 Обновить", command=self._refresh_all,
            fg_color="#00AAFF", hover_color="#0088DD",
            width=160, height=50, corner_radius=25,
            font=("Arial", 16, "bold")
        )
        self.fab.place(relx=0.98, rely=0.98, anchor="se")
    
    # === Загрузка данных ===
    
    def _load_data_async(self):
        """Асинхронная загрузка всех данных с мгновенным отображением"""
        self.controller.update_status("Загрузка...", "#FFFF00")
        
        def load_all():
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_currency = executor.submit(self._fetch_currency)
                future_weather = executor.submit(self._fetch_weather)
                future_cyber = executor.submit(self._fetch_news, "cyber")
                future_politics = executor.submit(self._fetch_news, "politics")
                future_economy = executor.submit(self._fetch_news, "economy")
                future_tech = executor.submit(self._fetch_news, "tech")
                
                futures = {
                    future_currency: "currency",
                    future_weather: "weather",
                    future_cyber: "news_cyber",
                    future_politics: "news_politics",
                    future_economy: "news_economy",
                    future_tech: "news_tech",
                }
                
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        if result:
                            if task == "weather":
                                self.after(0, lambda r=result: self._update_weather_ui(r))
                            elif task == "currency":
                                self.after(0, lambda r=result: self._update_currency_ui(r))
                            elif task.startswith("news_"):
                                topic = task.split("_")[1]
                                self.after(0, lambda r=result, t=topic: self._update_news_ui(r["items"], t))
                    except Exception as e:
                        print(f"Ошибка загрузки {task}: {e}")
            
            self.after(0, lambda: self.controller.update_status("Готово", "#00FF00"))
        
        threading.Thread(target=load_all, daemon=True).start()
    
    def _fetch_weather(self) -> Optional[Dict]:
        """Получение погоды через API"""
        try:
            get_weather_data = _get_weather_module()
            # ИСПРАВЛЕНО: используем _driver_lock для консистентности
            with self._driver_lock:
                data = get_weather_data(None, self.cache["weather"]["city"])
            self.cache["weather"]["data"] = data
            print(f"[Weather] Получено: {data.get('temp', 'N/A')}")
            return data
        except Exception as e:
            print(f"[Weather] Ошибка: {e}")
            return None
    
    def _fetch_currency(self) -> Optional[Dict]:
        """Получение валют — с блокировкой драйвера"""
        try:
            get_currency_data = _get_currency_module()
            driver = getattr(self.controller, 'driver', None)
            
            if not driver:
                print("[Currency] Драйвер не доступен")
                return None
            
            with self._driver_lock:
                data = get_currency_data(driver)
            
            self.cache["currency"]["data"] = data
            print(f"[Currency] Получено: {data}")
            return data
        except Exception as e:
            print(f"[Currency] Ошибка: {e}")
            return None
    
    def _fetch_news(self, topic: str) -> Optional[Dict]:
        """Получение новостей — с блокировкой драйвера"""
        try:
            get_news_data = _get_news_module()
            driver = getattr(self.controller, 'driver', None)
            
            # ИСПРАВЛЕНО: добавлена блокировка драйвера для консистентности
            with self._driver_lock:
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
        self.weather_wind.configure(text=f"💨 {data.get('wind', '-- м/с')}")
        self.weather_humidity.configure(text=f"💧 {data.get('humidity', '--%')}")
        self.weather_city.configure(text=f"📍 {data.get('city', 'Белореченск')}")
        
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
        # ИСПРАВЛЕНО: добавлена проверка на None перед isinstance
        if data is None:
            print(f"[UI] Ошибка: данные валют отсутствуют (None)")
            return
        
        if not isinstance(data, dict):
            print(f"[UI] Ошибка: данные валют не являются словарем: {type(data)}")
            return
        
        for code in ["USD", "EUR", "BTC"]:
            if code in self.currency_cards and code in data:
                rate = data[code]
                self.currency_cards[code]["rate"].configure(text=str(rate))
                print(f"[UI] {code} обновлен: {rate}")
    
    def _update_news_ui(self, items: list, topic: str):
        """Обновить новости"""
        print(f"[UI] Обновление новостей {topic}: {len(items)} шт")
        colors = {"cyber": "#FF5252", "politics": "#448AFF", 
                 "economy": "#00C853", "tech": "#FF9100"}
        color = colors.get(topic, "gray")
        
        if topic != self.current_news_topic:
            return
        
        for widget in self.news_items_widgets:
            widget["title"].configure(text="")
            widget["time"].configure(text="")
            widget["indicator"].configure(fg_color="gray")
            widget["url"] = None
        
        for i, item in enumerate(items[:5]):
            if i < len(self.news_items_widgets):
                widget = self.news_items_widgets[i]
                title = item.get("title", "")
                if len(title) > 100:
                    title = title[:97] + "..."
                widget["title"].configure(text=title)
                widget["time"].configure(text="Только что")
                widget["indicator"].configure(fg_color=color)
                widget["url"] = item.get("url", item.get("summary", ""))
    
    # === Действия ===
    
    def _switch_news_topic(self, topic: str):
        """Переключение вкладки из кэша"""
        self.current_news_topic = topic
        self.news_topic_var.set(topic)
        
        for t in ["cyber", "politics", "economy", "tech"]:
            btn = getattr(self, f"news_btn_{t}", None)
            if btn:
                if t == topic:
                    btn.configure(fg_color="#00AAFF", text_color="white")
                else:
                    btn.configure(fg_color="transparent", text_color="#888888")
        
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
        
        for i in range(len(self.history_items) - 1, 0, -1):
            self.history_items[i]["time"].configure(
                text=self.history_items[i-1]["time"].cget("text"))
            self.history_items[i]["desc"].configure(
                text=self.history_items[i-1]["desc"].cget("text"))
        
        self.history_items[0]["time"].configure(text=now)
        self.history_items[0]["desc"].configure(
            text=f"#{self.request_count} Обновление")
        
        self._load_data_async()
    
    def _change_city(self):
        """Сменить город"""
        dialog = ctk.CTkInputDialog(text="Введите город:", title="Смена города")
        dialog.geometry("900x450")
        
        dialog.update()
        
        def scale_widgets(widget):
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.configure(font=("Arial", 48, "bold"))
                elif isinstance(child, ctk.CTkEntry):
                    child.configure(height=90, font=("Arial", 42))
                elif isinstance(child, ctk.CTkButton):
                    child.configure(height=90, font=("Arial", 42))
                scale_widgets(child)
        
        scale_widgets(dialog)
        
        city = dialog.get_input()
        # ИСПРАВЛЕНО: проверка на None и пустую строку
        if city and city.strip():
            self.cache["weather"]["city"] = city.strip()
            threading.Thread(target=self._load_data_async, daemon=True).start()
    
    def _open_news(self, index: int):
        """Открыть новость"""
        if index < len(self.news_items_widgets):
            url = self.news_items_widgets[index].get("url")
            if url and url.startswith("http"):
                webbrowser.open(url)
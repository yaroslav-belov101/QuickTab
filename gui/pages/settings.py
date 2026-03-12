import customtkinter as ctk
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from .base_page import BasePage


class SettingsPage(BasePage):
    """Страница настроек приложения с полным функционалом"""
    
    # Коэффициент масштабирования шрифтов
    FONT_SCALE = 1.5
    
    # Базовые размеры шрифтов (будут умножены на FONT_SCALE)
    FONT_SIZES = {
        "title": int(32 * FONT_SCALE),           # 48
        "header": int(22 * FONT_SCALE),            # 33
        "section_title": int(28 * FONT_SCALE),     # 42
        "label": int(16 * FONT_SCALE),             # 24
        "entry": int(13 * FONT_SCALE),             # 20
        "button": int(16 * FONT_SCALE),            # 24
        "small": int(12 * FONT_SCALE),             # 18
        "status": int(13 * FONT_SCALE),            # 20
    }
    
    # Конфигурация тем
    THEMES = {
        "Системная": "system",
        "Тёмная": "dark", 
        "Светлая": "light"
    }
    
    # Конфигурация цветовых схем
    COLOR_SCHEMES = {
        "Синяя": {
            "primary": "#00AAFF",
            "primary_hover": "#0088DD",
            "secondary": "#0066AA",
            "accent": "#00CCFF"
        },
        "Зелёная": {
            "primary": "#00C851",
            "primary_hover": "#00AA44",
            "secondary": "#008833",
            "accent": "#00DD66"
        },
        "Тёмно-синяя": {
            "primary": "#1E88E5",
            "primary_hover": "#1565C0",
            "secondary": "#0D47A1",
            "accent": "#42A5F5"
        },
        "Оранжевая": {
            "primary": "#FF6B35",
            "primary_hover": "#E55A2B",
            "secondary": "#CC4A1A",
            "accent": "#FF8C61"
        },
        "Фиолетовая": {
            "primary": "#9C27B0",
            "primary_hover": "#7B1FA2",
            "secondary": "#4A148C",
            "accent": "#CE93D8"
        }
    }
    
    # Путь к файлу конфигурации
    CONFIG_FILE = Path("config/settings.json")
    
    # Настройки по умолчанию
    DEFAULT_SETTINGS = {
        "theme": "Тёмная",
        "color_scheme": "Синяя",
        "headless": True,
        "user_agent": "",
        "default_city": "Белореченск",
        "cache_enabled": True,
        "auto_update_interval": 5,  # минуты
        "window_size": "1200x800",
        "font_scale": 1.0,
        "animations_enabled": True
    }
    
    def __init__(self, parent, controller=None, **kwargs):
        self.settings: Dict[str, Any] = {}
        self.callbacks: list[Callable] = []  # Callbacks для обновления других страниц
        super().__init__(parent, controller, **kwargs)
        
    def create_widgets(self):
        """Создание всех виджетов страницы"""
        # Загрузка настроек при инициализации
        self.load_settings()
        
        # Контейнер с прокруткой для адаптивности
        self.create_scrollable_container()
        
        # Заголовок
        self.create_header()
        
        # Основной контейнер для секций
        self.sections_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.sections_container.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Секции настроек в виде карточек
        self.create_appearance_card()
        self.create_browser_card()
        self.create_data_card()
        self.create_advanced_card()
        
        # Кнопки действий (фиксированные внизу)
        self.create_action_buttons()
        
        # Статус-бар
        self.create_status_bar()
        
        # Применение текущих настроек к UI
        self.apply_settings_to_ui()
    
    def create_scrollable_container(self):
        """Создание прокручиваемого контейнера"""
        # Главный фрейм прокрутки
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self.get_color("primary"),
            scrollbar_button_hover_color=self.get_color("primary_hover")
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_header(self):
        """Создание заголовка страницы"""
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Иконка настроек с анимацией
        self.settings_icon = ctk.CTkLabel(
            header_frame,
            text="⚙️",
            font=("Segoe UI Emoji", int(48 * self.FONT_SCALE)),
            text_color=self.get_color("primary")
        )
        self.settings_icon.pack(side="left", padx=(0, 15))
        
        # Заголовок
        title = ctk.CTkLabel(
            header_frame,
            text="НАСТРОЙКИ",
            font=("Helvetica", self.FONT_SIZES["title"], "bold"),
            text_color="#FFFFFF"
        )
        title.pack(side="left")
        
        # Кнопка сброса в заголовке
        reset_icon_btn = ctk.CTkButton(
            header_frame,
            text="↺",
            width=int(40 * self.FONT_SCALE),
            height=int(40 * self.FONT_SCALE),
            font=("Helvetica", int(20 * self.FONT_SCALE)),
            fg_color="transparent",
            hover_color="#444444",
            command=self.reset_settings,
            corner_radius=20
        )
        reset_icon_btn.pack(side="right", padx=5)
        
        # Tooltip для кнопки сброса
        self.create_tooltip(reset_icon_btn, "Сбросить настройки по умолчанию")
    
    def create_card(self, parent, title: str, icon: str) -> ctk.CTkFrame:
        """Создание карточки секции с современным дизайном"""
        # Внешняя тень/рамка
        card_outer = ctk.CTkFrame(
            parent,
            fg_color=self.get_color("secondary"),
            corner_radius=16,
            border_width=2,
            border_color=self.get_color("primary")
        )
        card_outer.pack(fill="x", padx=10, pady=15)
        
        # Внутренний контейнер
        card = ctk.CTkFrame(card_outer, fg_color="#2a2a2a", corner_radius=14)
        card.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Заголовок карточки
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 15))
        
        # Иконка
        icon_label = ctk.CTkLabel(
            header,
            text=icon,
            font=("Segoe UI Emoji", int(28 * self.FONT_SCALE)),
            text_color=self.get_color("primary")
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        # Текст заголовка
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=("Helvetica", self.FONT_SIZES["header"], "bold"),
            text_color=self.get_color("primary")
        )
        title_label.pack(side="left")
        
        # Линия-разделитель под заголовком
        separator = ctk.CTkFrame(
            card,
            height=2,
            fg_color=self.get_color("secondary")
        )
        separator.pack(fill="x", padx=20, pady=(0, 15))
        
        # Контейнер для содержимого
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        return content
    
    def create_appearance_card(self):
        """Карточка настроек внешнего вида"""
        content = self.create_card(self.sections_container, "Внешний вид", "🎨")
        
        # Сетка для настроек
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)
        
        # Тема
        row = 0
        ctk.CTkLabel(
            content,
            text="Тема оформления:",
            font=("Helvetica", self.FONT_SIZES["label"]),
            text_color="#CCCCCC"
        ).grid(row=row, column=0, sticky="w", pady=12)
        
        self.theme_var = ctk.StringVar(value=self.settings.get("theme", "Тёмная"))
        self.theme_menu = ctk.CTkOptionMenu(
            content,
            values=list(self.THEMES.keys()),
            variable=self.theme_var,
            width=int(200 * self.FONT_SCALE),
            height=int(35 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["entry"]),
            dropdown_font=("Helvetica", int(13 * self.FONT_SCALE)),
            fg_color=self.get_color("primary"),
            button_color=self.get_color("primary_hover"),
            button_hover_color=self.get_color("accent"),
            dropdown_fg_color="#2a2a2a",
            dropdown_hover_color=self.get_color("secondary"),
            command=self.on_theme_change
        )
        self.theme_menu.grid(row=row, column=1, sticky="e", pady=12)
        
        # Цветовая схема
        row += 1
        ctk.CTkLabel(
            content,
            text="Акцентный цвет:",
            font=("Helvetica", self.FONT_SIZES["label"]),
            text_color="#CCCCCC"
        ).grid(row=row, column=0, sticky="w", pady=12)
        
        self.color_var = ctk.StringVar(value=self.settings.get("color_scheme", "Синяя"))
        self.color_menu = ctk.CTkOptionMenu(
            content,
            values=list(self.COLOR_SCHEMES.keys()),
            variable=self.color_var,
            width=int(200 * self.FONT_SCALE),
            height=int(35 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["entry"]),
            dropdown_font=("Helvetica", int(13 * self.FONT_SCALE)),
            fg_color=self.get_color("primary"),
            button_color=self.get_color("primary_hover"),
            button_hover_color=self.get_color("accent"),
            dropdown_fg_color="#2a2a2a",
            dropdown_hover_color=self.get_color("secondary"),
            command=self.on_color_change
        )
        self.color_menu.grid(row=row, column=1, sticky="e", pady=12)
        
        # Превью цвета
        row += 1
        self.color_preview = ctk.CTkFrame(
            content,
            width=int(30 * self.FONT_SCALE),
            height=int(30 * self.FONT_SCALE),
            corner_radius=15,
            fg_color=self.get_color("primary"),
            border_width=2,
            border_color="#FFFFFF"
        )
        self.color_preview.grid(row=row, column=1, sticky="e", pady=5)
        
        # Масштаб шрифта
        row += 1
        ctk.CTkLabel(
            content,
            text="Масштаб интерфейса:",
            font=("Helvetica", self.FONT_SIZES["label"]),
            text_color="#CCCCCC"
        ).grid(row=row, column=0, sticky="w", pady=12)
        
        self.scale_var = ctk.DoubleVar(value=self.settings.get("font_scale", 1.0))
        self.scale_slider = ctk.CTkSlider(
            content,
            from_=0.8,
            to=1.3,
            number_of_steps=5,
            variable=self.scale_var,
            width=int(200 * self.FONT_SCALE),
            progress_color=self.get_color("primary"),
            button_color=self.get_color("accent"),
            button_hover_color="#FFFFFF",
            command=self.on_scale_change
        )
        self.scale_slider.grid(row=row, column=1, sticky="e", pady=12)
        
        # Метка значения масштаба
        self.scale_label = ctk.CTkLabel(
            content,
            text=f"{int(self.scale_var.get() * 100)}%",
            font=("Helvetica", self.FONT_SIZES["entry"]),
            text_color=self.get_color("primary")
        )
        self.scale_label.grid(row=row, column=1, sticky="e", padx=(0, int(210 * self.FONT_SCALE)), pady=12)
    
    def create_browser_card(self):
        """Карточка настроек браузера"""
        content = self.create_card(self.sections_container, "Браузер и сеть", "🌐")
        
        # Headless режим
        self.headless_var = ctk.BooleanVar(value=self.settings.get("headless", True))
        
        headless_frame = ctk.CTkFrame(content, fg_color="transparent")
        headless_frame.pack(fill="x", pady=10)
        
        self.headless_switch = ctk.CTkSwitch(
            headless_frame,
            text="Фоновый режим (headless)",
            variable=self.headless_var,
            font=("Helvetica", self.FONT_SIZES["label"]),
            progress_color=self.get_color("primary"),
            button_color=self.get_color("accent"),
            button_hover_color="#FFFFFF",
            command=self.on_headless_toggle
        )
        self.headless_switch.pack(side="left")
        
        # Описание
        ctk.CTkLabel(
            headless_frame,
            text="• Браузер работает скрытно",
            font=("Helvetica", self.FONT_SIZES["small"]),
            text_color="#888888"
        ).pack(side="right")
        
        # User-Agent
        ua_frame = ctk.CTkFrame(content, fg_color="transparent")
        ua_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(
            ua_frame,
            text="User-Agent:",
            font=("Helvetica", self.FONT_SIZES["label"]),
            text_color="#CCCCCC"
        ).pack(anchor="w")
        
        self.ua_entry = ctk.CTkEntry(
            ua_frame,
            placeholder_text="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
            font=("Helvetica", self.FONT_SIZES["entry"]),
            height=int(40 * self.FONT_SCALE),
            fg_color="#333333",
            border_color=self.get_color("secondary"),
            border_width=2
        )
        self.ua_entry.pack(fill="x", pady=(8, 0))
        self.ua_entry.insert(0, self.settings.get("user_agent", ""))
        
        # Кнопка сброса UA
        ua_reset_btn = ctk.CTkButton(
            ua_frame,
            text="🔄 Сбросить",
            width=int(100 * self.FONT_SCALE),
            height=int(30 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["small"]),
            fg_color="transparent",
            hover_color="#444444",
            command=lambda: self.ua_entry.delete(0, "end")
        )
        ua_reset_btn.pack(anchor="e", pady=(5, 0))
    
    def create_data_card(self):
        """Карточка настроек данных"""
        content = self.create_card(self.sections_container, "Данные и локация", "💾")
        
        # Город по умолчанию
        city_frame = ctk.CTkFrame(content, fg_color="transparent")
        city_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            city_frame,
            text="Город по умолчанию:",
            font=("Helvetica", self.FONT_SIZES["label"]),
            text_color="#CCCCCC"
        ).pack(side="left")
        
        self.city_entry = ctk.CTkEntry(
            city_frame,
            placeholder_text="Например: Москва",
            width=int(250 * self.FONT_SCALE),
            height=int(40 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["entry"]),
            fg_color="#333333",
            border_color=self.get_color("secondary"),
            border_width=2
        )
        self.city_entry.pack(side="right")
        self.city_entry.insert(0, self.settings.get("default_city", "Белореченск"))
        
        # Кэширование
        cache_frame = ctk.CTkFrame(content, fg_color="transparent")
        cache_frame.pack(fill="x", pady=15)
        
        self.cache_var = ctk.BooleanVar(value=self.settings.get("cache_enabled", True))
        
        self.cache_switch = ctk.CTkSwitch(
            cache_frame,
            text="Кэширование данных",
            variable=self.cache_var,
            font=("Helvetica", self.FONT_SIZES["label"]),
            progress_color=self.get_color("primary"),
            button_color=self.get_color("accent"),
            button_hover_color="#FFFFFF"
        )
        self.cache_switch.pack(side="left")
        
        ctk.CTkLabel(
            cache_frame,
            text="• Ускоряет загрузку виджетов",
            font=("Helvetica", self.FONT_SIZES["small"]),
            text_color="#888888"
        ).pack(side="right")
        
        # Интервал обновления
        interval_frame = ctk.CTkFrame(content, fg_color="transparent")
        interval_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(
            interval_frame,
            text="Интервал автообновления:",
            font=("Helvetica", self.FONT_SIZES["label"]),
            text_color="#CCCCCC"
        ).pack(side="left")
        
        self.interval_var = ctk.IntVar(value=self.settings.get("auto_update_interval", 5))
        self.interval_slider = ctk.CTkSlider(
            interval_frame,
            from_=1,
            to=60,
            number_of_steps=59,
            variable=self.interval_var,
            width=int(200 * self.FONT_SCALE),
            progress_color=self.get_color("primary"),
            button_color=self.get_color("accent"),
            command=self.on_interval_change
        )
        self.interval_slider.pack(side="right")
        
        self.interval_label = ctk.CTkLabel(
            interval_frame,
            text=f"{self.interval_var.get()} мин",
            font=("Helvetica", self.FONT_SIZES["entry"]),
            width=int(60 * self.FONT_SCALE),
            text_color=self.get_color("primary")
        )
        self.interval_label.pack(side="right", padx=10)
    
    def create_advanced_card(self):
        """Карточка продвинутых настроек"""
        content = self.create_card(self.sections_container, "Продвинутые", "⚡")
        
        # Анимации
        anim_frame = ctk.CTkFrame(content, fg_color="transparent")
        anim_frame.pack(fill="x", pady=10)
        
        self.animations_var = ctk.BooleanVar(value=self.settings.get("animations_enabled", True))
        
        self.animations_switch = ctk.CTkSwitch(
            anim_frame,
            text="Анимации интерфейса",
            variable=self.animations_var,
            font=("Helvetica", self.FONT_SIZES["label"]),
            progress_color=self.get_color("primary"),
            button_color=self.get_color("accent"),
            button_hover_color="#FFFFFF"
        )
        self.animations_switch.pack(side="left")
        
        # Размер окна
        size_frame = ctk.CTkFrame(content, fg_color="transparent")
        size_frame.pack(fill="x", pady=15)
        
        ctk.CTkLabel(
            size_frame,
            text="Размер окна:",
            font=("Helvetica", self.FONT_SIZES["label"]),
            text_color="#CCCCCC"
        ).pack(side="left")
        
        self.size_var = ctk.StringVar(value=self.settings.get("window_size", "1200x800"))
        size_menu = ctk.CTkOptionMenu(
            size_frame,
            values=["1000x700", "1200x800", "1400x900", "1600x1000", "1920x1080"],
            variable=self.size_var,
            width=int(150 * self.FONT_SCALE),
            height=int(35 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["entry"]),
            fg_color=self.get_color("primary"),
            button_color=self.get_color("primary_hover")
        )
        size_menu.pack(side="right")
    
    def create_action_buttons(self):
        """Создание панели кнопок действий"""
        # Фиксированный фрейм внизу окна
        btn_container = ctk.CTkFrame(self, fg_color="#1a1a1a", height=int(80 * self.FONT_SCALE))
        btn_container.pack(fill="x", side="bottom", pady=0)
        btn_container.pack_propagate(False)
        
        # Внутренний контейнер для центрирования
        btn_frame = ctk.CTkFrame(btn_container, fg_color="transparent")
        btn_frame.pack(expand=True)
        
        # Кнопка сохранения с градиентным эффектом
        self.save_btn = ctk.CTkButton(
            btn_frame,
            text="💾  СОХРАНИТЬ",
            command=self.save_settings,
            width=int(180 * self.FONT_SCALE),
            height=int(45 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["button"], "bold"),
            fg_color=self.get_color("primary"),
            hover_color=self.get_color("primary_hover"),
            corner_radius=12,
            border_width=0
        )
        self.save_btn.pack(side="left", padx=10)
        
        # Кнопка сброса
        self.reset_btn = ctk.CTkButton(
            btn_frame,
            text="↺  СБРОСИТЬ",
            command=self.reset_settings,
            width=int(150 * self.FONT_SCALE),
            height=int(45 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["button"]),
            fg_color="#444444",
            hover_color="#666666",
            corner_radius=12
        )
        self.reset_btn.pack(side="left", padx=10)
        
        # Кнопка экспорта
        self.export_btn = ctk.CTkButton(
            btn_frame,
            text="📤  ЭКСПОРТ",
            command=self.export_settings,
            width=int(150 * self.FONT_SCALE),
            height=int(45 * self.FONT_SCALE),
            font=("Helvetica", self.FONT_SIZES["button"]),
            fg_color="#555555",
            hover_color="#777777",
            corner_radius=12
        )
        self.export_btn.pack(side="left", padx=10)
    
    def create_status_bar(self):
        """Создание статус-бара"""
        self.status_bar = ctk.CTkLabel(
            self,
            text="",
            font=("Helvetica", self.FONT_SIZES["status"]),
            text_color="#888888",
            height=int(25 * self.FONT_SCALE)
        )
        self.status_bar.pack(fill="x", side="bottom", padx=20, pady=(0, 5))
    
    def create_tooltip(self, widget, text: str):
        """Создание всплывающей подсказки (упрощенная версия)"""
        # В реальном приложении здесь будет полноценный tooltip
        pass
    
    # ==================== ОБРАБОТЧИКИ СОБЫТИЙ ====================
    
    def on_theme_change(self, value: str):
        """Обработчик изменения темы"""
        self.show_status(f"Тема изменена на: {value}")
        # Применяем тему сразу для предпросмотра
        ctk.set_appearance_mode(self.THEMES.get(value, "dark"))
    
    def on_color_change(self, value: str):
        """Обработчик изменения цветовой схемы"""
        colors = self.COLOR_SCHEMES.get(value, self.COLOR_SCHEMES["Синяя"])
        self.color_preview.configure(fg_color=colors["primary"])
        self.show_status(f"Цветовая схема: {value}")
        
        # Обновляем цвета всех интерактивных элементов
        self.update_ui_colors(colors)
    
    def on_scale_change(self, value: float):
        """Обработчик изменения масштаба"""
        self.scale_label.configure(text=f"{int(value * 100)}%")
    
    def on_interval_change(self, value: float):
        """Обработчик изменения интервала"""
        self.interval_label.configure(text=f"{int(value)} мин")
    
    def on_headless_toggle(self):
        """Обработчик переключения headless режима"""
        status = "включен" if self.headless_var.get() else "выключен"
        self.show_status(f"Фоновый режим {status}")
    
    # ==================== УПРАВЛЕНИЕ НАСТРОЙКАМИ ====================
    
    def get_color(self, color_type: str = "primary") -> str:
        """Получение текущего цвета из активной схемы"""
        scheme = self.COLOR_SCHEMES.get(
            getattr(self, 'color_var', None) and self.color_var.get() or "Синяя",
            self.COLOR_SCHEMES["Синяя"]
        )
        return scheme.get(color_type, "#00AAFF")
    
    def update_ui_colors(self, colors: Dict[str, str]):
        """Обновление цветов всех UI элементов"""
        # Обновляем выпадающие меню
        for menu in [self.theme_menu, self.color_menu]:
            if menu:
                menu.configure(
                    fg_color=colors["primary"],
                    button_color=colors["primary_hover"],
                    button_hover_color=colors["accent"]
                )
        
        # Обновляем слайдеры
        for slider in [getattr(self, 'scale_slider', None), getattr(self, 'interval_slider', None)]:
            if slider:
                slider.configure(
                    progress_color=colors["primary"],
                    button_color=colors["accent"]
                )
        
        # Обновляем переключатели
        for switch in [getattr(self, 'headless_switch', None), 
                      getattr(self, 'cache_switch', None),
                      getattr(self, 'animations_switch', None)]:
            if switch:
                switch.configure(
                    progress_color=colors["primary"],
                    button_color=colors["accent"]
                )
        
        # Обновляем кнопку сохранения
        if hasattr(self, 'save_btn'):
            self.save_btn.configure(
                fg_color=colors["primary"],
                hover_color=colors["primary_hover"]
            )
        
        # Обновляем метки с цветами
        if hasattr(self, 'scale_label'):
            self.scale_label.configure(text_color=colors["primary"])
        if hasattr(self, 'interval_label'):
            self.interval_label.configure(text_color=colors["primary"])
    
    def load_settings(self) -> Dict[str, Any]:
        """Загрузка настроек из файла"""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Объединяем с дефолтными (для новых полей)
                    self.settings = {**self.DEFAULT_SETTINGS, **loaded}
            else:
                self.settings = self.DEFAULT_SETTINGS.copy()
                self.save_settings_to_file()  # Создаем файл с дефолтами
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
        
        return self.settings
    
    def save_settings_to_file(self) -> bool:
        """Сохранение настроек в JSON файл"""
        try:
            # Создаем директорию если нужно
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False
    
    def collect_settings_from_ui(self) -> Dict[str, Any]:
        """Сбор текущих значений из UI"""
        return {
            "theme": self.theme_var.get(),
            "color_scheme": self.color_var.get(),
            "headless": self.headless_var.get(),
            "user_agent": self.ua_entry.get().strip(),
            "default_city": self.city_entry.get().strip() or "Белореченск",
            "cache_enabled": self.cache_var.get(),
            "auto_update_interval": int(self.interval_var.get()),
            "window_size": self.size_var.get(),
            "font_scale": round(self.scale_var.get(), 2),
            "animations_enabled": self.animations_var.get()
        }
    
    def save_settings(self):
        """Сохранение настроек с валидацией и применением"""
        # Собираем данные из UI
        new_settings = self.collect_settings_from_ui()
        
        # Валидация
        errors = self.validate_settings(new_settings)
        if errors:
            self.show_status(f"❌ Ошибка: {errors[0]}", error=True)
            return
        
        # Сохраняем
        self.settings = new_settings
        if self.save_settings_to_file():
            self.show_status("✅ Настройки сохранены!", success=True)
            
            # Применяем критические настройки сразу
            self.apply_critical_settings()
            
            # Уведомляем другие компоненты
            self.notify_settings_changed()
        else:
            self.show_status("❌ Ошибка сохранения файла", error=True)
    
    def validate_settings(self, settings: Dict[str, Any]) -> list[str]:
        """Валидация настроек"""
        errors = []
        
        # Проверка города
        if len(settings["default_city"]) < 2:
            errors.append("Название города слишком короткое")
        
        # Проверка User-Agent (если указан)
        if settings["user_agent"] and len(settings["user_agent"]) < 10:
            errors.append("User-Agent слишком короткий")
        
        # Проверка интервала
        if not (1 <= settings["auto_update_interval"] <= 60):
            errors.append("Интервал должен быть от 1 до 60 минут")
        
        return errors
    
    def apply_critical_settings(self):
        """Применение критических настроек, требующих перезагрузки/переконфигурации"""
        # Тема
        ctk.set_appearance_mode(self.THEMES.get(self.settings["theme"], "dark"))
        
        # Масштаб (требует перезагрузки для полного применения)
        ctk.set_widget_scaling(self.settings["font_scale"])
        
        # Здесь можно добавить вызовы к другим модулям
        # Например: обновление конфигурации парсеров, изменение города погоды и т.д.
    
    def notify_settings_changed(self):
        """Уведомление подписчиков об изменении настроек"""
        for callback in self.callbacks:
            try:
                callback(self.settings)
            except Exception as e:
                print(f"Ошибка в callback настроек: {e}")
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Регистрация callback для уведомлений об изменениях"""
        self.callbacks.append(callback)
    
    def reset_settings(self):
        """Сброс к настройкам по умолчанию с подтверждением"""
        # В реальном приложении здесь должен быть диалог подтверждения
        # Для простоты — сразу сбрасываем
        
        self.settings = self.DEFAULT_SETTINGS.copy()
        
        # Обновляем UI
        self.theme_var.set(self.settings["theme"])
        self.color_var.set(self.settings["color_scheme"])
        self.headless_var.set(self.settings["headless"])
        self.ua_entry.delete(0, "end")
        self.city_entry.delete(0, "end")
        self.city_entry.insert(0, self.settings["default_city"])
        self.cache_var.set(self.settings["cache_enabled"])
        self.interval_var.set(self.settings["auto_update_interval"])
        self.scale_var.set(self.settings["font_scale"])
        self.animations_var.set(self.settings["animations_enabled"])
        self.size_var.set(self.settings["window_size"])
        
        # Обновляем метки
        self.scale_label.configure(text=f"{int(self.scale_var.get() * 100)}%")
        self.interval_label.configure(text=f"{self.interval_var.get()} мин")
        
        # Сбрасываем цвета
        self.update_ui_colors(self.COLOR_SCHEMES[self.settings["color_scheme"]])
        
        self.show_status("↺ Настройки сброшены (не забудьте сохранить)", success=True)
    
    def export_settings(self):
        """Экспорт настроек в выбираемое место"""
        # Здесь должен быть диалог выбора файла
        # Для примера — просто копируем в config/settings_backup.json
        backup_path = Path("config/settings_backup.json")
        try:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            self.show_status(f"📤 Экспортировано в {backup_path}", success=True)
        except Exception as e:
            self.show_status(f"❌ Ошибка экспорта: {e}", error=True)
    
    def apply_settings_to_ui(self):
        """Применение загруженных настроек к UI элементам"""
        # Устанавливаем тему
        ctk.set_appearance_mode(self.THEMES.get(self.settings["theme"], "dark"))
        
        # Устанавливаем масштаб
        ctk.set_widget_scaling(self.settings["font_scale"])
        
        # Обновляем цвета
        colors = self.COLOR_SCHEMES.get(
            self.settings["color_scheme"], 
            self.COLOR_SCHEMES["Синяя"]
        )
        self.update_ui_colors(colors)
    
    def show_status(self, message: str, success: bool = False, error: bool = False):
        """Отображение статусного сообщения"""
        color = "#888888"  # Обычный
        if success:
            color = "#00FF00"
        elif error:
            color = "#FF4444"
        
        self.status_bar.configure(text=message, text_color=color)
        
        # Автоочистка через 5 секунд
        self.after(5000, lambda: self.status_bar.configure(text="", text_color="#888888"))
    
    def get_settings(self) -> Dict[str, Any]:
        """Публичный метод для получения текущих настроек"""
        return self.settings.copy()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получение конкретной настройки"""
        return self.settings.get(key, default)
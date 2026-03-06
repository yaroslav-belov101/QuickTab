import customtkinter as ctk
from .base_page import BasePage

class SettingsPage(BasePage):
    """Страница настроек приложения"""
    
    THEMES = ["Системная", "Тёмная", "Светлая"]
    COLORS = ["Синяя", "Зелёная", "Тёмно-синяя"]
    
    def create_widgets(self):
        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="⚙️ НАСТРОЙКИ",
            font=("Arial", 36, "bold"),
            text_color="#FFFFFF"
        )
        title.pack(pady=20)
        
        # Контейнер для настроек
        settings_container = ctk.CTkFrame(self, fg_color="#2a2a2a")
        settings_container.pack(pady=20, padx=50, fill="both", expand=True)
        
        # Внешний вид
        self.create_appearance_settings(settings_container)
        
        # Разделитель
        separator = ctk.CTkFrame(settings_container, height=2, fg_color="#444444")
        separator.pack(fill="x", padx=20, pady=20)
        
        # Браузер
        self.create_browser_settings(settings_container)
        
        # Разделитель
        separator2 = ctk.CTkFrame(settings_container, height=2, fg_color="#444444")
        separator2.pack(fill="x", padx=20, pady=20)
        
        # Данные
        self.create_data_settings(settings_container)
        
        # Кнопки действий
        self.create_action_buttons()
    
    def create_appearance_settings(self, parent):
        """Настройки внешнего вида"""
        section_title = ctk.CTkLabel(
            parent,
            text="🎨 Внешний вид",
            font=("Arial", 28, "bold"),
            text_color="#00AAFF"
        )
        section_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Тема
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x", padx=20, pady=5)
        
        theme_label = ctk.CTkLabel(theme_frame, text="Тема:", font=("Arial", 24))
        theme_label.pack(side="left")
        
        self.theme_var = ctk.StringVar(value="Тёмная")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=self.THEMES,
            variable=self.theme_var,
            width=200
        )
        theme_menu.pack(side="right")
        
        # Цветовая схема
        color_frame = ctk.CTkFrame(parent, fg_color="transparent")
        color_frame.pack(fill="x", padx=20, pady=5)
        
        color_label = ctk.CTkLabel(color_frame, text="Цветовая схема:", font=("Arial", 24))
        color_label.pack(side="left")
        
        self.color_var = ctk.StringVar(value="Синяя")
        color_menu = ctk.CTkOptionMenu(
            color_frame,
            values=self.COLORS,
            variable=self.color_var,
            width=200
        )
        color_menu.pack(side="right")
    
    def create_browser_settings(self, parent):
        """Настройки браузера"""
        section_title = ctk.CTkLabel(
            parent,
            text="🌐 Браузер",
            font=("Arial", 28, "bold"),
            text_color="#00AAFF"
        )
        section_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Headless режим
        self.headless_var = ctk.BooleanVar(value=True)
        headless_cb = ctk.CTkCheckBox(
            parent,
            text="Фоновый режим (headless)",
            font=("Arial", 24),
            variable=self.headless_var
        )
        headless_cb.pack(anchor="w", padx=20, pady=5)
        
        # User-Agent
        ua_frame = ctk.CTkFrame(parent, fg_color="transparent")
        ua_frame.pack(fill="x", padx=20, pady=5)
        
        ua_label = ctk.CTkLabel(ua_frame, text="User-Agent:", font=("Arial", 24))
        ua_label.pack(anchor="w")
        
        self.ua_entry = ctk.CTkEntry(
            ua_frame,
            placeholder_text="Mozilla/5.0...",
            font=("Arial", 20)
        )
        self.ua_entry.pack(fill="x", pady=(5, 0))
    
    def create_data_settings(self, parent):
        """Настройки данных"""
        section_title = ctk.CTkLabel(
            parent,
            text="💾 Данные",
            font=("Arial", 28, "bold"),
            text_color="#00AAFF"
        )
        section_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Город по умолчанию
        city_frame = ctk.CTkFrame(parent, fg_color="transparent")
        city_frame.pack(fill="x", padx=20, pady=5)
        
        city_label = ctk.CTkLabel(city_frame, text="Город по умолчанию:", font=("Arial", 24))
        city_label.pack(side="left")
        
        self.city_entry = ctk.CTkEntry(city_frame, placeholder_text="Белореченск", width=200)
        self.city_entry.pack(side="right")
        
        # Кэширование
        self.cache_var = ctk.BooleanVar(value=True)
        cache_cb = ctk.CTkCheckBox(
            parent,
            text="Кэшировать данные",
            font=("Arial", 24),
            variable=self.cache_var
        )
        cache_cb.pack(anchor="w", padx=20, pady=5)
    
    def create_action_buttons(self):
        """Кнопки действий"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Сохранить",
            command=self.save_settings,
            fg_color="#00AAFF",
            hover_color="#0088DD",
            height=50,
            font=("Arial", 24)
        )
        save_btn.pack(side="left", padx=10)
        
        reset_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Сбросить",
            command=self.reset_settings,
            fg_color="#666666",
            hover_color="#888888",
            height=50,
            font=("Arial", 24)
        )
        reset_btn.pack(side="left", padx=10)
    
    def save_settings(self):
        """Сохранить настройки"""
        # Здесь логика сохранения в файл/базу данных
        self.update_status("Настройки сохранены!", "#00FF00")
    
    def reset_settings(self):
        """Сбросить настройки"""
        self.theme_var.set("Тёмная")
        self.color_var.set("Синяя")
        self.headless_var.set(True)
        self.ua_entry.delete(0, "end")
        self.city_entry.delete(0, "end")
        self.cache_var.set(True)
        self.update_status("Настройки сброшены", "#FFFF00")
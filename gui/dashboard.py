import customtkinter as ctk
from typing import Callable, Dict


class Dashboard(ctk.CTkFrame):
    """
    Компактный черный дашборд с фиксированной навигацией
    """
    
    MENU_ITEMS = [
        ("home", "🏠", "Главная"),
        ("search", "🔍", "Поиск"),
        ("settings", "⚙️", "Настройки"),
        ("about", "ℹ️", "О программе"),
    ]
    
    def __init__(self, parent, navigation_callback: Callable[[str], None], 
                 version: str = "1.0.0", **kwargs):
        super().__init__(parent, fg_color="#0D0D0D", width=320, **kwargs)
        
        self.pack_propagate(False)
        self.navigation_callback = navigation_callback
        self.version = version
        self.active_button: str = "home"
        self.menu_buttons: Dict[str, ctk.CTkButton] = {}
        
        self.create_header()
        self.create_menu()
        self.create_footer()
    
    def create_header(self):
        """Заголовок"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(header, text="⚡", font=("Arial", 56)).pack()
        ctk.CTkLabel(header, text="QuickTab", 
                    font=("Arial", 36, "bold"),
                    text_color="#00AAFF").pack(pady=(5, 0))
        ctk.CTkLabel(header, text="Быстрый доступ к инфо", 
                    font=("Arial", 16),
                    text_color="#666666").pack()

    
    def create_menu(self):
        """Навигация - НЕ растягивается, фиксированная позиция"""
        # Контейнер без expand=True
        menu = ctk.CTkFrame(self, fg_color="transparent")
        menu.pack(fill="x", padx=15, pady=(5, 0))
        
        ctk.CTkLabel(menu, text="НАВИГАЦИЯ", 
                    font=("Arial", 14, "bold"),
                    text_color="#444444").pack(anchor="w", pady=(0, 10))
        
        for page_id, icon, label in self.MENU_ITEMS:
            btn = self._create_menu_button(menu, page_id, icon, label)
            btn.pack(fill="x", pady=4)
            self.menu_buttons[page_id] = btn
        
        self._update_button_styles()
    
    def _create_menu_button(self, parent, page_id: str, icon: str, label: str):
        """Кнопка меню"""
        
        def on_click():
            self.active_button = page_id
            self._update_button_styles()
            self.navigation_callback(page_id)
        
        btn = ctk.CTkButton(
            parent,
            text=f"{icon}  {label}",
            command=on_click,
            font=("Arial", 22, "bold"),
            height=60,
            fg_color="#1A1A1A",
            hover_color="#2A2A2A",
            text_color="#888888",
            anchor="w",
            corner_radius=12
        )
        
        btn.indicator = ctk.CTkFrame(btn, fg_color="#00AAFF", width=5, corner_radius=3)
        
        return btn
    
    def _update_button_styles(self):
        """Обновить стили кнопок"""
        for page_id, button in self.menu_buttons.items():
            indicator = button.indicator
            
            if page_id == self.active_button:
                button.configure(
                    fg_color="#00AAFF",
                    text_color="white",
                    hover_color="#0088DD"
                )
                indicator.place(relx=0.02, rely=0.5, anchor="w", relheight=0.6)
            else:
                button.configure(
                    fg_color="#1A1A1A",
                    text_color="#888888",
                    hover_color="#2A2A2A"
                )
                indicator.place_forget()
    
    def create_footer(self):
        """Футер - прижат к низу через place"""
        # Создаем контейнер для футера внизу
        footer_container = ctk.CTkFrame(self, fg_color="transparent")
        footer_container.pack(side="bottom", fill="x", padx=15, pady=15)
        
        footer = ctk.CTkFrame(footer_container, fg_color="#1A1A1A", corner_radius=15)
        footer.pack(fill="x")
        
        ctk.CTkLabel(footer, text=f"v{self.version}", 
                    font=("Arial", 16),
                    text_color="#555555").pack(pady=(10, 5))
        
        self.status_label = ctk.CTkLabel(footer, text="🟢 Система активна", 
                                        font=("Arial", 14),
                                        text_color="#00C853")
        self.status_label.pack(pady=(0, 10))
    
    def set_active_button(self, page_id: str):
        """Установить активную кнопку"""
        if page_id in self.menu_buttons:
            self.active_button = page_id
            self._update_button_styles()
    
    def update_status(self, text: str, color: str = "#00C853"):
        """Обновить статус"""
        self.status_label.configure(text=text, text_color=color)
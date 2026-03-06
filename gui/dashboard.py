import customtkinter as ctk
from typing import Callable, Dict


class Dashboard(ctk.CTkFrame):
    """
    Левая панель навигации (дашборд) с логотипом, 
    меню навигации и информацией о версии.
    
    Ширина увеличена на 10%, меню удлинено по высоте.
    """
    
    # Конфигурация кнопок меню
    MENU_ITEMS = [
        ("home", "🏠", "Главная"),
        ("search", "🔍", "Поиск"),
        ("settings", "⚙️", "Настройки"),
        ("about", "ℹ️", "О программе"),
    ]
    
    def __init__(self, parent, navigation_callback: Callable[[str], None], 
                 version: str = "0.5.0", **kwargs):
        # Увеличиваем ширину на 10% (было ~250, стало ~275)
        # Можно также задать фиксированную ширину через width
        super().__init__(parent, fg_color="#2a2a2a", border_width=1, 
                        border_color="#444444", width=275, **kwargs)
        
        self.pack_propagate(False)  # Фиксируем ширину
        
        self.navigation_callback = navigation_callback
        self.version = version
        self.active_button: str = "home"
        self.menu_buttons: Dict[str, ctk.CTkButton] = {}
        
        self.create_header()
        self.create_menu()
        self.create_footer()
    
    def create_header(self):
        """Создает заголовок с логотипом"""
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=15, padx=15, fill="x")
        
        # Логотип/Иконка
        logo_label = ctk.CTkLabel(
            header_frame,
            text="⚡",
            font=("Arial", 52),  # Увеличили размер
            text_color="#00FFFF"
        )
        logo_label.pack()
        
        # Название приложения
        title_label = ctk.CTkLabel(
            header_frame,
            text="QuickTab",
            font=("Arial", 30, "bold"),  # Увеличили размер
            text_color="#00FFFF"
        )
        title_label.pack(pady=(5, 0))
        
        # Подзаголовок
        subtitle = ctk.CTkLabel(
            header_frame,
            text="Быстрый доступ к инфо",
            font=("Arial", 13),  # Увеличили размер
            text_color="#888888"
        )
        subtitle.pack()
    
    def create_menu(self):
        """Создает меню навигации — УДЛИНЕННОЕ ПО ВЫСОТЕ"""
        
        # Контейнер меню — увеличиваем отступы для большей высоты
        menu_container = ctk.CTkFrame(self, fg_color="#3a3a3a", border_width=1,
                                     border_color="#555555")
        # Увеличиваем отступы сверху и снизу
        menu_container.pack(pady=25, padx=15, fill="x")
        
        # Заголовок меню
        menu_title = ctk.CTkLabel(
            menu_container,
            text="МЕНЮ",
            font=("Arial", 16, "bold"),  # Увеличили размер
            text_color="#FFFFFF"
        )
        menu_title.pack(pady=12)  # Увеличили отступ
        
        # Разделитель
        separator = ctk.CTkFrame(menu_container, height=2, fg_color="#555555")
        separator.pack(fill="x", padx=10, pady=(0, 12))  # Увеличили отступ
        
        # Кнопки меню — УВЕЛИЧИВАЕМ ВЫСОТУ КАЖДОЙ КНОПКИ
        for page_id, icon, label in self.MENU_ITEMS:
            btn = self.create_menu_button(menu_container, page_id, icon, label)
            # Увеличиваем отступы между кнопками для большей высоты меню
            btn.pack(pady=5, padx=10, fill="x")  # Было pady=3, стало pady=5
            self.menu_buttons[page_id] = btn
        
        # Устанавливаем начальное активное состояние
        self.update_button_styles()
        
        # Добавляем растягивающийся пустой фрейм для заполнения пространства
        spacer = ctk.CTkFrame(menu_container, fg_color="transparent", height=30)
        spacer.pack(fill="x", pady=5)
    
    def create_menu_button(self, parent, page_id: str, icon: str, 
                          label: str) -> ctk.CTkButton:
        """
        Создает кнопку меню навигации — УВЕЛИЧЕННАЯ ВЫСОТА
        
        Args:
            parent: Родительский виджет
            page_id: Идентификатор страницы
            icon: Эмодзи-иконка
            label: Текст кнопки
            
        Returns:
            Созданная кнопка
        """
        
        def on_click():
            self.active_button = page_id
            self.update_button_styles()
            self.navigation_callback(page_id)
        
        button = ctk.CTkButton(
            parent,
            text=f"{icon}  {label}",
            command=on_click,
            font=("Arial", 18, "bold"),  # Увеличили шрифт (было 16)
            height=55,  # УВЕЛИЧИЛИ ВЫСОТУ (было 45)
            fg_color="transparent",
            hover_color="#666666",
            anchor="w",
            corner_radius=10  # Увеличили скругление
        )
        
        return button
    
    def update_button_styles(self):
        """Обновляет стили кнопок в зависимости от активной страницы"""
        
        for page_id, button in self.menu_buttons.items():
            if page_id == self.active_button:
                # Активная кнопка
                button.configure(
                    fg_color="#00AAFF",
                    hover_color="#0088DD",
                    text_color="#FFFFFF"
                )
            else:
                # Неактивная кнопка
                button.configure(
                    fg_color="#4a4a4a",
                    hover_color="#666666",
                    text_color="#CCCCCC"
                )
    
    def set_active_button(self, page_id: str):
        """
        Устанавливает активную кнопку программно
        
        Args:
            page_id: Идентификатор страницы
        """
        if page_id in self.menu_buttons:
            self.active_button = page_id
            self.update_button_styles()
    
    def create_footer(self):
        """Создает нижнюю часть дашборда с информацией"""
        
        footer_frame = ctk.CTkFrame(self, fg_color="#3a3a3a", border_width=1,
        border_color="#555555")
        footer_frame.pack(side="bottom", fill="x", padx=15, pady=15)
        
        # Версия
        version_label = ctk.CTkLabel(
            footer_frame,
            text=f"v{self.version}",
            font=("Arial", 13),  # Увеличили размер
            text_color="#888888"
        )
        version_label.pack(pady=10)
        
        # Статус соединения
        self.connection_status = ctk.CTkLabel(
            footer_frame,
            text="🟢 Драйвер активен",
            font=("Arial", 12),  # Увеличили размер
            text_color="#00FF00"
        )
        self.connection_status.pack(pady=(0, 10))
    
    def update_connection_status(self, connected: bool):
        """
        Обновляет индикатор статуса соединения
        
        Args:
            connected: True если соединение активно
        """
        if connected:
            self.connection_status.configure(
                text="🟢 Драйвер активен",
                text_color="#00FF00"
            )
        else:
            self.connection_status.configure(
                text="🔴 Драйвер неактивен",
                text_color="#FF0000"
            )
    
    def highlight_button(self, page_id: str, highlight: bool = True):
        """
        Временно подсвечивает кнопку (для уведомлений)
        
        Args:
            page_id: Идентификатор страницы
            highlight: True для подсветки, False для сброса
        """
        if page_id not in self.menu_buttons:
            return
        
        button = self.menu_buttons[page_id]
        
        if highlight and page_id != self.active_button:
            button.configure(fg_color="#FFAA00", hover_color="#DD8800")
        else:
            self.update_button_styles()
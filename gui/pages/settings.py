import customtkinter as ctk
from .base_page import BasePage


class SettingsPage(BasePage):
    """Страница настроек — только интерфейс"""
    
    def create_widgets(self):
        # Главный контейнер
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # Заголовок
        header = ctk.CTkFrame(main_frame, fg_color="transparent", height=120)
        header.pack(fill="x", padx=30, pady=(20, 10))
        header.pack_propagate(False)
        
        icon_frame = ctk.CTkFrame(header, fg_color="transparent")
        icon_frame.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(icon_frame, text="⚙️", font=("Segoe UI Emoji", 64)).pack()
        
        text_frame = ctk.CTkFrame(header, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text="Настройки приложения",
            font=("Arial", 42, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text="Настройте QuickTab под свои предпочтения",
            font=("Arial", 18),
            text_color="#888888"
        ).pack(anchor="w", pady=(5, 0))
        
        # Плашка "В разработке"
        dev_banner = ctk.CTkFrame(
            main_frame,
            fg_color="#FF6D00",
            corner_radius=15,
            height=60
        )
        dev_banner.pack(fill="x", padx=30, pady=(0, 10))
        dev_banner.pack_propagate(False)
        
        ctk.CTkLabel(
            dev_banner,
            text="🚧 В РАЗРАБОТКЕ",
            font=("Arial", 28, "bold"),
            text_color="#FFFFFF"
        ).pack(expand=True)
        
        # Скроллируемая область
        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Карточка внешнего вида
        self._create_card(scroll, "Внешний вид", "🎨")
        
        # Карточка данных
        self._create_card(scroll, "Данные и обновления", "💾")
        
        # Карточка поведения
        self._create_card(scroll, "Поведение приложения", "⚡")
        
        # Карточка системы
        self._create_card(scroll, "Система", "ℹ️")
    
    def _create_card(self, parent, title: str, icon: str):
        """Создаёт карточку секции"""
        # Внешняя рамка
        shadow = ctk.CTkFrame(
            parent, 
            fg_color="#242424",
            corner_radius=20
        )
        shadow.pack(fill="x", pady=15)
        
        # Внутренняя карточка
        card = ctk.CTkFrame(
            shadow, 
            fg_color="#242424", 
            corner_radius=18,
            border_width=1,
            border_color="#333333"
        )
        card.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Заголовок
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(25, 15))
        
        # Иконка в круге
        icon_circle = ctk.CTkFrame(
            header,
            width=50,
            height=50,
            corner_radius=25,
            fg_color="#00AAFF"
        )
        icon_circle.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(
            icon_circle,
            text=icon,
            font=("Segoe UI Emoji", 28),
            text_color="#FFFFFF"
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Текст заголовка
        text_frame = ctk.CTkFrame(header, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text=title,
            font=("Arial", 26, "bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")
        
        # Разделитель
        ctk.CTkFrame(
            card, 
            height=2, 
            fg_color="#333333",
            corner_radius=1
        ).pack(fill="x", padx=25, pady=(0, 20))


# Фабричная функция
def create_settings_page(parent, controller):
    return SettingsPage(parent, controller)
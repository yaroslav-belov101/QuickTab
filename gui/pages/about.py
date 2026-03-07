import customtkinter as ctk
from .base_page import BasePage

class AboutPage(BasePage):
    """Страница информации о программе"""
    
    def create_widgets(self):
        # Контейнер для центрирования
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True)
        
        # Логотип/Иконка
        icon_label = ctk.CTkLabel(
            container,
            text="⚡",
            font=("Arial", 120),
            text_color="#00AAFF"
        )
        icon_label.pack(pady=20)
        
        # Название
        name_label = ctk.CTkLabel(
            container,
            text="QuickTab",
            font=("Arial", 48, "bold"),
            text_color="#FFFFFF"
        )
        name_label.pack()
        
        # Версия
        try:
            from quicktab import __version__
        except ImportError:
            __version__ = "0.6.0"
        
        version_label = ctk.CTkLabel(
            container,
            text=f"версия {__version__}",
            font=("Arial", 24),
            text_color="#888888"
        )
        version_label.pack(pady=5)
        
        # Описание
        desc_frame = ctk.CTkFrame(container, fg_color="#2a2a2a", border_width=1, border_color="#444444")
        desc_frame.pack(pady=30, padx=50, fill="x")
        
        description = (
            "Быстрый доступ к информации:\n\n"
            "• 🌤️ Погода в реальном времени\n"
            "• 💱 Актуальные курсы валют\n"
            "• 📰 Новости по категориям\n\n"
            "Создано для удобства и скорости!"
        )
        
        desc_label = ctk.CTkLabel(
            desc_frame,
            text=description,
            font=("Arial", 24),
            text_color="#FFFFFF",
            justify="center"
        )
        desc_label.pack(pady=30, padx=30)
        
        # Технологии
        tech_frame = ctk.CTkFrame(container, fg_color="transparent")
        tech_frame.pack(pady=10)
        
        tech_label = ctk.CTkLabel(
            tech_frame,
            text="Технологии:",
            font=("Arial", 20, "bold"),
            text_color="#888888"
        )
        tech_label.pack()
        
        techs = ctk.CTkLabel(
            tech_frame,
            text="Python • CustomTkinter • Selenium",
            font=("Arial", 18),
            text_color="#666666"
        )
        techs.pack()
        
        # Копирайт
        copyright_label = ctk.CTkLabel(
            container,
            text="© 2024 QuickTab Team",
            font=("Arial", 16),
            text_color="#444444"
        )
        copyright_label.pack(pady=30)
        
        # Кнопка проверки обновлений
        update_btn = ctk.CTkButton(
            container,
            text="🔄 Проверить обновления",
            command=self.check_updates,
            fg_color="#4a4a4a",
            hover_color="#666666",
            height=40,
            font=("Arial", 20)
        )
        update_btn.pack(pady=10)
    
    def check_updates(self):
        """Проверить наличие обновлений"""
        import tkinter.messagebox as msgbox
        
        # Заглушка для проверки обновлений
        msgbox.showinfo(
            "Обновления",
            "У вас установлена последняя версия!\n\n"
            "Текущая версия: 0.6.0\n"
            "Последняя версия: 0.6.0"
        )
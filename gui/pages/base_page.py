import customtkinter as ctk
from abc import ABC, abstractmethod

class BasePage(ABC, ctk.CTkFrame):
    """Базовый класс для всех страниц приложения"""
    
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller  # Ссылка на главное приложение
        self.create_widgets()
    
    @abstractmethod
    def create_widgets(self):
        """Создание виджетов страницы — реализуется в дочерних классах"""
        pass
    
    def show(self):
        """Показать страницу"""
        self.pack(fill="both", expand=True)
    
    def hide(self):
        """Скрыть страницу"""
        self.pack_forget()
    
    def clear(self):
        """Очистить содержимое страницы"""
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()
    
    def get_driver(self):
        """Получить WebDriver из контроллера"""
        return getattr(self.controller, 'driver', None)
    
    def update_status(self, text, color="#FFFFFF"):
        """Обновить статус в главном окне"""
        if hasattr(self.controller, 'status_label'):
            self.controller.status_label.configure(text=text, text_color=color)
import customtkinter as ctk
import sys

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, '.')

from gui.dashboard import Dashboard
from gui.pages import HomePage, SearchPage, SettingsPage, AboutPage
from core.driver import DriverManager


class QuickTabGUI(ctk.CTk):
    """
    Главное окно приложения QuickTab.
    Управляет навигацией, страницами и глобальными ресурсами.
    """
    
    def __init__(self):
        super().__init__()
        
        # Настройки окна
        self.title("QuickTab")
        self.geometry("1200x700")
        self.minsize(800, 600)
        self.resizable(True, True)
        
        # Тема
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Версия
        try:
            from quicktab import __version__
        except ImportError:
            __version__ = "0.7.0"
        self.version = __version__
        
        # Обновляем заголовок с версией
        self.title(f"QuickTab v{self.version}")
        
        # Инициализация драйвера
        self.driver_manager = DriverManager()
        self.driver = self.driver_manager.init_driver()
        
        # Словарь страниц
        self.pages = {}
        self.current_page = None
        
        # Создание интерфейса
        self.create_layout()
        self.create_pages()
        
        # Обработчик закрытия
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Показываем главную страницу
        self.show_page("home")
        
        print(f"✅ QuickTab v{self.version} запущен!")
    
    def create_layout(self):
        """Создает общий макет окна с левой панелью и областью контента"""
        
        # Главный контейнер
        self.main_container = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.main_container.pack(fill="both", expand=True)
        
        # Настройка сетки
        self.main_container.grid_columnconfigure(0, weight=0, minsize=550)  # Дашборд фиксированной ширины
        self.main_container.grid_columnconfigure(1, weight=1)  # Контент растягивается
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Левая панель (дашборд)
        self.dashboard = Dashboard(
            self.main_container,
            navigation_callback=self.show_page,
            version=self.version
        )
        self.dashboard.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Правая область для страниц
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Статусная строка внизу
        self.status_frame = ctk.CTkFrame(self, fg_color="#2a2a2a", height=40)
        self.status_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="🟢 Готов к работе",
            font=("Arial", 14),
            text_color="#00FF00"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Счетчик запросов
        self.request_count_label = ctk.CTkLabel(
            self.status_frame,
            text="Запросов: 0",
            font=("Arial", 12),
            text_color="#888888"
        )
        self.request_count_label.pack(side="right", padx=10, pady=5)
    
    def create_pages(self):
        """Создает и сохраняет все страницы приложения"""
        
        self.pages = {
            "home": HomePage(self.content_frame, self),
            "search": SearchPage(self.content_frame, self),
            "settings": SettingsPage(self.content_frame, self),
            "about": AboutPage(self.content_frame, self)
        }
    
    def show_page(self, page_name: str):
        """
        Переключает отображаемую страницу
        
        Args:
            page_name: Имя страницы ('home', 'search', 'settings', 'about')
        """
        if page_name not in self.pages:
            print(f"❌ Страница '{page_name}' не найдена!")
            return
        
        # Скрываем текущую страницу
        if self.current_page:
            self.current_page.hide()
        
        # Показываем новую страницу
        self.current_page = self.pages[page_name]
        self.current_page.show()
        
        # Обновляем активную кнопку в дашборде
        self.dashboard.set_active_button(page_name)
        
        print(f"📄 Открыта страница: {page_name}")
    
    def update_status(self, text: str, color: str = "#FFFFFF"):
        """
        Обновляет текст статусной строки
        
        Args:
            text: Текст статуса
            color: Цвет текста (hex)
        """
        self.status_label.configure(text=text, text_color=color)
        self.update_idletasks()
    
    def increment_request_count(self):
        """Увеличивает счетчик запросов"""
        current = int(self.request_count_label.cget("text").split(": ")[1])
        new_count = current + 1
        self.request_count_label.configure(text=f"Запросов: {new_count}")
        return new_count
    
    def get_request_count(self) -> int:
        """Возвращает текущее количество запросов"""
        return int(self.request_count_label.cget("text").split(": ")[1])
    
    def on_closing(self):
        """Корректное закрытие приложения с очисткой ресурсов"""
        print("🛑 Завершение работы QuickTab...")
        
        try:
            # Закрываем драйвер
            self.driver_manager.close()
            
            # Сохраняем настройки если нужно
            
            print("✅ QuickTab корректно завершен!")
            
        except Exception as e:
            print(f"⚠️ Ошибка при закрытии: {e}")
        
        finally:
            self.destroy()
            sys.exit(0)


def main():
    """Точка входа для запуска GUI"""
    print("🚀 Запуск QuickTab...")
    app = QuickTabGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
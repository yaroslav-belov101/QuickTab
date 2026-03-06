import customtkinter as ctk
from .base_page import BasePage
from gui.components import SearchFilters

class SearchPage(BasePage):
    """Страница поиска по данным"""
    
    def create_widgets(self):
        # Заголовок
        title = ctk.CTkLabel(
            self,
            text="🔍 ПОИСК",
            font=("Arial", 36, "bold"),
            text_color="#00FFFF"
        )
        title.pack(pady=10)
        
        # Поле ввода
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Введите запрос для поиска...",
            font=("Arial", 28),
            height=50
        )
        self.search_entry.pack(pady=10, padx=20, fill="x")
        
        # Кнопка поиска
        search_btn = ctk.CTkButton(
            self,
            text="🔍 Искать",
            command=self.perform_search,
            fg_color="#00AAFF",
            hover_color="#0088DD",
            height=50,
            font=("Arial", 24)
        )
        search_btn.pack(pady=5, padx=20, fill="x")
        
        # Фильтры
        self.filters = SearchFilters(self)
        self.filters.pack(pady=10, padx=20, fill="x")
        
        # Результаты
        results_frame = ctk.CTkFrame(self, fg_color="#2a2a2a")
        results_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        results_title = ctk.CTkLabel(
            results_frame,
            text="Результаты:",
            font=("Arial", 28, "bold"),
            text_color="#FFFFFF"
        )
        results_title.pack(pady=5, anchor="w", padx=10)
        
        self.results_text = ctk.CTkTextbox(
            results_frame,
            font=("Arial", 24),
            height=200
        )
        self.results_text.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Начальный текст
        self.show_placeholder()
    
    def show_placeholder(self):
        """Показать текст-заглушку"""
        placeholder = (
            "Результаты поиска появятся здесь...\n\n"
            "Предлагаемые функции поиска:\n"
            "• Поиск по ключевым словам в новостях\n"
            "• Фильтрация погоды по городам\n"
            "• Поиск курсов конкретных валют\n"
            "• История запросов\n"
            "• Сохраненные поиски"
        )
        self.results_text.delete("0.0", "end")
        self.results_text.insert("0.0", placeholder)
    
    def perform_search(self):
        """Выполнить поиск"""
        query = self.search_entry.get().strip()
        
        if not query:
            self.results_text.delete("0.0", "end")
            self.results_text.insert("0.0", "Введите поисковый запрос!")
            return
        
        active_filters = self.filters.get_active_filters()
        filter_text = ", ".join(active_filters) if active_filters else "все источники"
        
        result_text = (
            f"Поиск по запросу: '{query}'\n"
            f"Фильтры: {filter_text}\n\n"
            f"Функционал поиска будет реализован в следующих версиях.\n\n"
            f"Предлагаемые возможности:\n"
            f"• Интеллектуальный поиск по всем источникам\n"
            f"• Фильтрация результатов\n"
            f"• Сохранение поисковых запросов\n"
            f"• Автодополнение\n"
            f"• Поиск в истории"
        )
        
        self.results_text.delete("0.0", "end")
        self.results_text.insert("0.0", result_text)
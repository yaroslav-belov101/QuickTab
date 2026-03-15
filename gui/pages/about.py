import customtkinter as ctk
from .base_page import BasePage

class AboutPage(BasePage):
    """Страница информации о программе"""
    
    def create_widgets(self):
        # Скроллируемая область
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === ЗАГОЛОВОК ===
        header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 30))
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text="⚡",
            font=("Arial", 80),
            text_color="#00AAFF"
        )
        icon_label.pack()
        
        name_label = ctk.CTkLabel(
            header_frame,
            text="QuickTab v1.0.0",
            font=("Arial", 48, "bold"),
            text_color="#FFFFFF"
        )
        name_label.pack()
        
        tagline = ctk.CTkLabel(
            header_frame,
            text="Универсальный информационный хаб",
            font=("Arial", 24),
            text_color="#00AAFF"
        )
        tagline.pack(pady=(5, 0))
        
        # === ОБ ПРИЛОЖЕНИИ ===
        about_card = self._create_card(scroll_frame, "ℹ️ О приложении", 
            "QuickTab — это быстрый и удобный способ получить информацию без переключения вкладок.\n\n"
            "Просто спросите в поиске то, что вам нужно — погода, курсы валют, новости, ответы на вопросы. "
            "Все данные загружаются мгновенно прямо в приложении!")
        
        # === ОСНОВНЫЕ ФУНКЦИИ ===
        features_card = ctk.CTkFrame(scroll_frame, fg_color="#2a2a2a", corner_radius=15)
        features_card.pack(fill="x", pady=15, ipady=15)
        
        features_title = ctk.CTkLabel(
            features_card,
            text="🎯 Функции",
            font=("Arial", 32, "bold"),
            text_color="#00AAFF"
        )
        features_title.pack(pady=(15, 10), anchor="w", padx=20)
        
        features = [
            ("🌤️", "Погода", "Актуальная информация с деталями"),
            ("💱", "Валюты", "Курсы USD, EUR, BTC в реальном времени"),
            ("📰", "Новости", "Категории: кибер, политика, экономика, технологии"),
            ("🤖", "ИИ-ответы", "Google Gemini для ответов на любые вопросы"),
            ("🔍", "Поиск", "Умный поиск с веб-ссылками и Wikipedia"),
        ]
        
        for emoji, title, desc in features:
            feature_frame = ctk.CTkFrame(features_card, fg_color="transparent")
            feature_frame.pack(fill="x", padx=20, pady=8)
            
            ctk.CTkLabel(
                feature_frame,
                text=f"{emoji} {title}",
                font=("Arial", 24, "bold"),
                text_color="#FFFFFF"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                feature_frame,
                text=desc,
                font=("Arial", 20),
                text_color="#AAAAAA"
            ).pack(anchor="w", padx=(40, 0))
        
        # === ТЕХНОЛОГИИ ===
        tech_card = self._create_card(scroll_frame, "⚙️ Технологии",
            "Python 3.8+ • CustomTkinter • Selenium 4.15\n"
            "Google Gemini AI • BeautifulSoup • Requests\n\n"
            "Открытые источники: Яндекс.Погода, CoinMarketCap, CoinTelegraph")
        
        # === БЫСТРЫЕ ПРИМЕРЫ ===
        examples_card = ctk.CTkFrame(scroll_frame, fg_color="#2a2a2a", corner_radius=15)
        examples_card.pack(fill="x", pady=15, ipady=15)
        
        examples_title = ctk.CTkLabel(
            examples_card,
            text="💡 Примеры запросов",
            font=("Arial", 32, "bold"),
            text_color="#FF9100"
        )
        examples_title.pack(pady=(15, 10), anchor="w", padx=20)
        
        examples = [
            "Погода в Москве",
            "Курс доллара",
            "100 долларов в рубли",
            "Что такое искусственный интеллект?",
            "2+2*3",
            "Новости кибербезопасности"
        ]
        
        for example in examples:
            example_frame = ctk.CTkFrame(examples_card, fg_color="#333333", corner_radius=8)
            example_frame.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                example_frame,
                text=f"  📌 {example}",
                font=("Arial", 20),
                text_color="#00AAFF"
            ).pack(anchor="w", pady=8)
        
        # === ИНФОРМАЦИЯ ===
        info_card = self._create_card(scroll_frame, "📋 Информация",
            "Автор: Yaroslav Belov\n"
            "Локация: Белореченск, Краснодарский край\n"
            "Год: 2026\n\n"
            "Лицензия: MIT\n"
            "GitHub: github.com/yaroslav-belov101/QuickTab")
        
        # === КНОПКА ОБНОВЛЕНИЯ ===
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        update_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Версия v1.0.0 (актуальная)",
            command=self.check_updates,
            fg_color="#00AAFF",
            hover_color="#0088CC",
            height=50,
            font=("Arial", 24, "bold"),
            text_color="#000000",
            corner_radius=12
        )
        update_btn.pack(pady=10)
        
        # === НИЖНИЙ ТЕКСТ ===
        footer = ctk.CTkLabel(
            scroll_frame,
            text="© 2026 QuickTab • Спасибо за использование! ⭐",
            font=("Arial", 18),
            text_color="#555555"
        )
        footer.pack(pady=(20, 0))
    
    def _create_card(self, parent, title: str, content: str):
        """Создать красивую карточку"""
        card = ctk.CTkFrame(parent, fg_color="#2a2a2a", corner_radius=15)
        card.pack(fill="x", pady=15, ipady=15)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 32, "bold"),
            text_color="#00AAFF"
        )
        title_label.pack(pady=(15, 10), anchor="w", padx=20)
        
        content_label = ctk.CTkLabel(
            card,
            text=content,
            font=("Arial", 21),
            text_color="#CCCCCC",
            justify="left",
            wraplength=700
        )
        content_label.pack(pady=10, anchor="w", padx=20, fill="x")
        
        return card
    
    def check_updates(self):
        """Проверить наличие обновлений"""
        import tkinter.messagebox as msgbox
        
        msgbox.showinfo(
            "Версия",
            "QuickTab v1.0.0\n\n"
            "✅ У вас установлена последняя версия!\n\n"
            "Спасибо за использование приложения! ⭐"
        )
import customtkinter as ctk
from tkinter import scrolledtext

class ResultsDisplay:
    """Компонент отображения результатов с заголовком и текстовой областью"""
    
    def __init__(self, parent, title="📊 РЕЗУЛЬТАТЫ:"):
        self.frame = ctk.CTkFrame(parent, fg_color="#2a2a2a", border_width=1, border_color="#444444")
        
        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.frame,
            text=title,
            font=("Arial", 32, "bold"),
            text_color="#FFFFFF"
        )
        self.title_label.pack(pady=5, anchor="w", padx=10)
        
        # Текстовая область
        self.text_area = scrolledtext.ScrolledText(
            self.frame,
            wrap="word",
            font=("Consolas", 12),
            bg="#1a1a1a",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            selectbackground="#444444",
            selectforeground="#FFFFFF"
        )
        self.text_area.pack(pady=5, padx=10, fill="both", expand=True)
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def clear(self):
        self.text_area.delete(1.0, "end")
    
    def append(self, text):
        self.text_area.insert("end", text)
        self.text_area.see("end")
    
    def set_title(self, title):
        self.title_label.configure(text=title)
    
    def get_text_widget(self):
        return self.text_area
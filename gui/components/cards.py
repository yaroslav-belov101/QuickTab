import customtkinter as ctk

class ModuleCard:
    """Карточка выбора модуля (погода/валюта)"""
    
    def __init__(self, parent, text, icon, command, font=("Arial", 32, "bold")):
        self.var = ctk.BooleanVar(value=False)
        self.command = command
        
        self.button = ctk.CTkButton(
            parent, 
            text=f"{icon} {text}",
            command=self.toggle,
            font=font,
            height=70,
            fg_color="#4a4a4a",
            hover_color="#666666"
        )
    
    def toggle(self):
        self.var.set(not self.var.get())
        self.update_color()
        if self.command:
            self.command()
    
    def update_color(self):
        if self.var.get():
            self.button.configure(fg_color="#00AAFF", hover_color="#0088DD")
        else:
            self.button.configure(fg_color="#4a4a4a", hover_color="#666666")
    
    def pack(self, **kwargs):
        self.button.pack(**kwargs)
    
    def get(self):
        return self.var.get()
    
    def set(self, value):
        self.var.set(value)
        self.update_color()


class NewsCardWithMenu:
    """Карточка новостей с выпадающим меню тем"""
    
    TOPICS = {
        "🛡️ Кибербезопасность": "cyber",
        "🌍 Политика": "politics", 
        "💰 Экономика": "economy",
        "🚀 Технологии": "tech"
    }
    
    def __init__(self, parent, command=None):
        self.var = ctk.BooleanVar(value=False)
        self.topic_var = ctk.StringVar(value="🛡️ Кибербезопасность")
        self.command = command
        
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        self.button = ctk.CTkButton(
            self.frame,
            text="📰 НОВОСТИ",
            command=self.toggle,
            font=("Arial", 32, "bold"),
            height=70,
            fg_color="#4a4a4a",
            hover_color="#666666"
        )
        self.button.pack(side="left", fill="x", expand=True)
        
        self.topic_menu = ctk.CTkOptionMenu(
            self.frame,
            values=list(self.TOPICS.keys()),
            variable=self.topic_var,
            state="disabled",
            fg_color="#4a4a4a",
            button_color="#666666",
            button_hover_color="#777777",
            width=250
        )
        self.topic_menu.pack(side="right", padx=(10, 0))
    
    def toggle(self):
        self.var.set(not self.var.get())
        self.update_state()
        if self.command:
            self.command()
    
    def update_state(self):
        if self.var.get():
            self.button.configure(fg_color="#00AAFF", hover_color="#0088DD")
            self.topic_menu.configure(state="normal")
        else:
            self.button.configure(fg_color="#4a4a4a", hover_color="#666666")
            self.topic_menu.configure(state="disabled")
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def get(self):
        return self.var.get()
    
    def get_topic(self):
        return self.TOPICS.get(self.topic_var.get(), "cyber")
    
    def set(self, value):
        self.var.set(value)
        self.update_state()
import customtkinter as ctk

class SearchFilters:
    """Панель фильтров для поиска"""
    
    FILTERS = [
        ("weather", "Погода", "🌤️"),
        ("currency", "Курсы", "💱"),
        ("news", "Новости", "📰")
    ]
    
    def __init__(self, parent, font=("Arial", 24)):
        self.frame = ctk.CTkFrame(parent, fg_color="#4a4a4a")
        self.checkboxes = {}
        self.vars = {}
        
        title = ctk.CTkLabel(self.frame, text="Фильтры:", font=(font[0], font[1], "bold"), text_color="#FFFFFF")
        title.pack(pady=5)
        
        for key, text, icon in self.FILTERS:
            var = ctk.BooleanVar(value=False)
            self.vars[key] = var
            
            cb = ctk.CTkCheckBox(
                self.frame,
                text=f"{icon} {text}",
                font=font,
                variable=var
            )
            cb.pack(pady=2, anchor="w", padx=10)
            self.checkboxes[key] = cb
    
    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
    
    def get_active_filters(self):
        """Возвращает список активных фильтров"""
        return [key for key, var in self.vars.items() if var.get()]
    
    def is_active(self, filter_name):
        return self.vars.get(filter_name, ctk.BooleanVar()).get()
    
    def set_filter(self, filter_name, value):
        if filter_name in self.vars:
            self.vars[filter_name].set(value)
    
    def reset(self):
        for var in self.vars.values():
            var.set(False)
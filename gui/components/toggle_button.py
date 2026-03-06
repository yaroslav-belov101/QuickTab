import customtkinter as ctk

class ToggleButton:
    """Кнопка с двумя состояниями (вкл/выкл)"""
    
    def __init__(self, parent, text, icon="", 
                 on_color="#00AAFF", off_color="#4a4a4a",
                 font=("Arial", 32, "bold"), height=70,
                 command=None):
        
        self.var = ctk.BooleanVar(value=False)
        self.on_color = on_color
        self.on_hover = self._darken(on_color)
        self.off_color = off_color
        self.off_hover = self._darken(off_color)
        self.command = command
        
        self.button = ctk.CTkButton(
            parent,
            text=f"{icon} {text}" if icon else text,
            command=self.toggle,
            font=font,
            height=height,
            fg_color=off_color,
            hover_color=self.off_hover
        )
    
    def _darken(self, hex_color, factor=0.8):
        """Затемняет цвет для hover-эффекта"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f'#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}'
    
    def toggle(self):
        self.var.set(not self.var.get())
        self._update_appearance()
        if self.command:
            self.command(self.var.get())
    
    def _update_appearance(self):
        if self.var.get():
            self.button.configure(fg_color=self.on_color, hover_color=self.on_hover)
        else:
            self.button.configure(fg_color=self.off_color, hover_color=self.off_hover)
    
    def pack(self, **kwargs):
        self.button.pack(**kwargs)
    
    def grid(self, **kwargs):
        self.button.grid(**kwargs)
    
    def get(self):
        return self.var.get()
    
    def set(self, value):
        self.var.set(value)
        self._update_appearance()
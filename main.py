import customtkinter as ctk
from utils import resource_path
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import inicializar
from views.login_view import LoginView
from views.home_view  import HomeView

ctk.set_appearance_mode("dark")
import os as _os
_theme_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "assets", "green_theme.json")
ctk.set_default_color_theme(_theme_path)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Achados e Perdidos")
        self.geometry("1100x660")
        self.minsize(1000, 580)
        self._usuario_logado = None

        # Ícone
        _base = os.path.dirname(os.path.abspath(__file__))
        _ico  = resource_path(os.path.join("assets", "icon.ico"))
        _png  = resource_path(os.path.join("assets", "icon.png"))
        try:
            if os.name == "nt" and os.path.exists(_ico):
                self.iconbitmap(_ico)
            elif os.path.exists(_png):
                from PIL import Image, ImageTk
                img = Image.open(_png).resize((64, 64))
                self._icon_img = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass

        # Banco seguro no AppData ao rodar como .exe
        import sys as _sys
        if getattr(_sys, "frozen", False):
            from database.db import mover_banco_para_appdata
            mover_banco_para_appdata()

        inicializar()
        self._mostrar_login()

    def _limpar_tela(self):
        for w in self.winfo_children():
            w.destroy()

    def _mostrar_login(self):
        self._limpar_tela()
        LoginView(self, on_login_success=self._apos_login)

    def _apos_login(self, usuario: dict):
        self._usuario_logado = usuario
        self._limpar_tela()
        HomeView(self, usuario=usuario, on_logout=self._mostrar_login)

    def on_closing(self):
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

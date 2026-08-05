import customtkinter as ctk
from tkinter import messagebox
import sys, os
from PIL import Image


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import autenticar_usuario
from utils import resource_path


class LoginView(ctk.CTkFrame):

    def __init__(self, master, on_login_success=None):
        super().__init__(master, fg_color="transparent")
        self.master           = master
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        card = ctk.CTkFrame(self, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.configure(width=420, height=460)
        card.grid_propagate(False)

        # Ícone personalizado
        _base = resource_path(os.path.join("assets", "AP.png"))
        try:
            img = ctk.CTkImage(Image.open(_base), size=(72, 72))
            ctk.CTkLabel(card, image=img, text="").pack(pady=(32, 0))
        except Exception:
            ctk.CTkLabel(card, text="🔍", font=ctk.CTkFont(size=52)).pack(pady=(32, 0))

        ctk.CTkLabel(card, text="Achados e Perdidos",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(card, text="Faça login para continuar",
                     font=ctk.CTkFont(size=13), text_color="gray").pack(pady=(0, 24))

        self.entry_usuario = ctk.CTkEntry(card, placeholder_text="Usuário",
                                           width=260, height=42, font=ctk.CTkFont(size=14))
        self.entry_usuario.pack(pady=(0, 12))

        self.entry_senha = ctk.CTkEntry(card, placeholder_text="Senha",
                                         show="•", width=260, height=42, font=ctk.CTkFont(size=14))
        self.entry_senha.pack(pady=(0, 6))

        self.mostrar_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Mostrar senha", variable=self.mostrar_var,
                        command=self._toggle_senha, font=ctk.CTkFont(size=12), width=300,
                        ).pack(pady=(0, 20))

        self.btn_entrar = ctk.CTkButton(card, text="Entrar", width=250, height=44,
                                         font=ctk.CTkFont(size=15, weight="bold"),
                                         command=self._fazer_login)
        self.btn_entrar.pack(pady=(0, 10))

        self.lbl_erro = ctk.CTkLabel(card, text="", text_color="#e05c5c",
                                      font=ctk.CTkFont(size=12))
        self.lbl_erro.pack()

        self.entry_senha.bind("<Return>",   lambda _: self._fazer_login())
        self.entry_usuario.bind("<Return>", lambda _: self.entry_senha.focus())
        self.entry_usuario.focus()

    def _toggle_senha(self):
        self.entry_senha.configure(show="" if self.mostrar_var.get() else "•")

    def _fazer_login(self):
        nome  = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()
        if not nome or not senha:
            self.lbl_erro.configure(text="Preencha usuário e senha."); return
        self.btn_entrar.configure(state="disabled", text="Verificando…")
        self.after(100, lambda: self._autenticar(nome, senha))

    def _autenticar(self, nome, senha):
        # Login case-insensitive: busca o usuário ignorando maiúsculas
        from database.db import get_conn
        conn = get_conn()
        import hashlib
        h = hashlib.sha256(senha.encode()).hexdigest()
        row = conn.execute(
            "SELECT * FROM usuarios WHERE LOWER(nome) = LOWER(?) AND senha = ?",
            (nome, h)
        ).fetchone()
        conn.close()
        usuario = dict(row) if row else None

        if usuario:
            self.lbl_erro.configure(text="")
            if self.on_login_success:
                self.on_login_success(usuario)
        else:
            self.btn_entrar.configure(state="normal", text="Entrar")
            self.lbl_erro.configure(text="Usuário ou senha incorretos.")
            self.entry_senha.delete(0, "end")
            self.entry_senha.focus()

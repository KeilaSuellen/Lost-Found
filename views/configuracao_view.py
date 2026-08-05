import customtkinter as ctk
from tkinter import filedialog, messagebox
import base64, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import obter_config, salvar_config
from utils import logo_padrao_b64


def _logo_padrao_b64() -> str:
    """Logo usado antes de existir configuração salva: o próprio ícone do app (AP.png)."""
    return logo_padrao_b64()


class ConfiguracaoView(ctk.CTkFrame):
    """Tela para o administrador escolher o logo e o nome da empresa
    que aparecem no formulário impresso de retirada."""

    def __init__(self, master, usuario: dict):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self._logo_b64 = obter_config("logo_b64", _logo_padrao_b64())
        self._build_ui()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        ctk.CTkLabel(self, text="Configurações do Formulário",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     ).pack(pady=(24, 4), anchor="w", padx=32)
        ctk.CTkLabel(self, text="Define o logo e o nome que aparecem no cabeçalho do formulário impresso de retirada.",
                     font=ctk.CTkFont(size=12), text_color="gray",
                     ).pack(anchor="w", padx=32, pady=(0, 20))

        card = ctk.CTkFrame(self, corner_radius=10)
        card.pack(fill="x", padx=32)

        # Logo
        ctk.CTkLabel(card, text="Logo", font=ctk.CTkFont(size=11), text_color="gray",
                     ).pack(anchor="w", padx=16, pady=(16, 4))
        logo_row = ctk.CTkFrame(card, fg_color="transparent")
        logo_row.pack(fill="x", padx=16, pady=(0, 16))

        self._preview = ctk.CTkLabel(logo_row, text="", width=140, height=48,
                                      fg_color="#222", corner_radius=6)
        self._preview.pack(side="left")
        self._atualizar_preview()

        ctk.CTkButton(logo_row, text="Escolher Logo...", width=160,
                      command=self._escolher_logo).pack(side="left", padx=(16, 8))
        ctk.CTkButton(logo_row, text="Remover", width=100, fg_color="transparent",
                      border_width=1, command=self._remover_logo).pack(side="left")

        # Nome da empresa / cliente
        ctk.CTkLabel(card, text="Nome da Empresa / Cliente", font=ctk.CTkFont(size=11),
                     text_color="gray").pack(anchor="w", padx=16, pady=(4, 4))
        self.e_empresa = ctk.CTkEntry(card, height=38, placeholder_text="Ex: Nome da Empresa")
        self.e_empresa.insert(0, obter_config("nome_empresa", "Empresa XYZ"))
        self.e_empresa.pack(fill="x", padx=16, pady=(0, 12))

        # Local / cidade
        ctk.CTkLabel(card, text="Local / Cidade", font=ctk.CTkFont(size=11),
                     text_color="gray").pack(anchor="w", padx=16, pady=(0, 4))
        self.e_site = ctk.CTkEntry(card, height=38, placeholder_text="Ex: São Paulo, SP")
        self.e_site.insert(0, obter_config("site", "São Paulo, SP"))
        self.e_site.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(self, text="Salvar", width=160, height=38,
                      command=self._salvar).pack(anchor="w", padx=32, pady=20)

    def _atualizar_preview(self):
        try:
            if self._logo_b64:
                import io
                from PIL import Image
                img_bytes = base64.b64decode(self._logo_b64)
                img = Image.open(io.BytesIO(img_bytes))
                img.thumbnail((132, 44))
                ctk_img = ctk.CTkImage(img, size=img.size)
                self._preview.configure(image=ctk_img, text="")
                self._preview.image = ctk_img
            else:
                self._preview.configure(image=None, text="sem logo")
        except Exception:
            self._preview.configure(image=None, text="inválido")

    def _escolher_logo(self):
        caminho = filedialog.askopenfilename(
            title="Escolher logo",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg")]
        )
        if not caminho:
            return
        try:
            with open(caminho, "rb") as f:
                self._logo_b64 = base64.b64encode(f.read()).decode("ascii")
            self._atualizar_preview()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar a imagem:\n{e}")

    def _remover_logo(self):
        self._logo_b64 = ""
        self._atualizar_preview()

    def _salvar(self):
        salvar_config("logo_b64", self._logo_b64)
        salvar_config("nome_empresa", self.e_empresa.get().strip())
        salvar_config("site", self.e_site.get().strip())
        messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")

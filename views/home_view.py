import customtkinter as ctk
import os, sys
from PIL import Image
from utils import resource_path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from views.cadastro_objeto_view     import CadastroObjetoView
from views.lista_objetos_view       import ListaObjetosView
from views.historico_retiradas_view import HistoricoRetiradasView
from views.retirada_view            import RetiradaView
from views.usuarios_view            import UsuariosView
from views.exportacao_view          import ExportacaoView
from views.log_atividades_view      import LogAtividadesView
from views.configuracao_view        import ConfiguracaoView

_BASE = resource_path("assets")

def _ico(nome, size=28):
    try:
        return ctk.CTkImage(Image.open(resource_path(os.path.join("assets", f"{nome}.png"))), size=(size, size))
    except Exception:
        return None


class HomeView(ctk.CTkFrame):

    def __init__(self, master, usuario: dict, on_logout=None):
        super().__init__(master, fg_color="transparent")
        self.usuario   = usuario
        self.on_logout = on_logout
        self._build_ui()
        self._navegar("lista")

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo no topo da sidebar
        try:
            img_logo = ctk.CTkImage(
                Image.open(resource_path(os.path.join("assets", "AP.png"))), size=(52, 52))
            ctk.CTkLabel(self.sidebar, image=img_logo, text="").pack(pady=(24, 0))
        except Exception:
            ctk.CTkLabel(self.sidebar, text="🔍", font=ctk.CTkFont(size=36)).pack(pady=(24, 0))

        ctk.CTkLabel(self.sidebar, text="Achados e\nPerdidos",
                     font=ctk.CTkFont(size=14, weight="bold"), justify="center",
                     ).pack(pady=(6, 20))

        # Menus
        MENU = [
            ("lista",    "lista",    "Objetos"),
            ("mala", "cadastro", "Cadastrar"),
            ("retirada", "retiradas","Retiradas"),
        ]
        MENU_ADMIN = [
            ("lupa",    "exportar", "Exportar"),
            ("usuario", "usuarios", "Usuários"),
            ("lista",   "log",      "Log"),
            ("usuario", "config",   "Configurações"),
        ]

        self._botoes = {}
        itens = MENU + (MENU_ADMIN if self.usuario["nivel"] == "Administrador" else [])
        for ico_nome, chave, label in itens:
            ico = _ico(ico_nome, 22)
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {label}",
                image=ico, compound="left",
                anchor="w", height=44, corner_radius=8,
                fg_color="transparent",
                hover_color=("#0F6E56","#0A4D36"),
                font=ctk.CTkFont(size=13),
                command=lambda c=chave: self._navegar(c),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._botoes[chave] = btn

        # Rodapé sidebar
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray30").pack(
            fill="x", padx=16, pady=12, side="bottom")
        info = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        info.pack(side="bottom", fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(info, text=f"👤  {self.usuario['nome']}",
                     font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=self.usuario["nivel"],
                     font=ctk.CTkFont(size=11), text_color="gray", anchor="w").pack(fill="x", pady=(2,6))
        ctk.CTkButton(info, text="Sair", height=32, fg_color="transparent",
                      border_width=1, command=self._logout).pack(fill="x")

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(side="left", expand=True, fill="both")

    def _get_content(self):
        for w in self._content.winfo_children():
            w.destroy()
        f = ctk.CTkFrame(self._content, fg_color="transparent")
        f.pack(expand=True, fill="both")
        return f

    def _marcar_botao(self, chave):
        for c, btn in self._botoes.items():
            btn.configure(fg_color="#0F6E56" if c == chave else "transparent")

    def _navegar(self, chave):
        self._marcar_botao(chave)
        content = self._get_content()
        if chave == "lista":
            ListaObjetosView(content, usuario=self.usuario,
                             on_registrar_retirada=self._abrir_retirada)
        elif chave == "cadastro":
            CadastroObjetoView(content, usuario=self.usuario,
                               on_salvo=lambda: self._navegar("lista"))
        elif chave == "retiradas":
            HistoricoRetiradasView(content, usuario=self.usuario)
        elif chave == "exportar":
            if self.usuario["nivel"] != "Administrador": return
            ExportacaoView(content, usuario=self.usuario,
                           on_concluido=lambda: self._navegar("lista"))
        elif chave == "usuarios":
            if self.usuario["nivel"] != "Administrador": return
            UsuariosView(content, usuario=self.usuario)
        elif chave == "log":
            if self.usuario["nivel"] != "Administrador": return
            LogAtividadesView(content, usuario=self.usuario)
        elif chave == "config":
            if self.usuario["nivel"] != "Administrador": return
            ConfiguracaoView(content, usuario=self.usuario)

    def _abrir_retirada(self, objeto):
        self._marcar_botao("retiradas")
        content = self._get_content()
        RetiradaView(content, usuario=self.usuario, objeto=objeto,
                     on_concluido=lambda: self._navegar("lista"))

    def _logout(self):
        self.destroy()
        if self.on_logout: self.on_logout()

import customtkinter as ctk
from tkinter import messagebox
import datetime, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import inserir_objeto, proximo_id_objeto
from utils import aplicar_mascara_data


class CadastroObjetoView(ctk.CTkFrame):
    """Formulário de cadastro de objeto encontrado."""

    def __init__(self, master, usuario: dict, on_salvo=None):
        super().__init__(master, fg_color="transparent")
        self.usuario  = usuario
        self.on_salvo = on_salvo
        self._build_ui()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        ctk.CTkLabel(self, text="Cadastrar Objeto",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     ).pack(pady=(24, 4), anchor="w", padx=32)
        ctk.CTkLabel(self, text=f"ID gerado automaticamente: {proximo_id_objeto()}",
                     font=ctk.CTkFont(size=12), text_color="gray",
                     ).pack(anchor="w", padx=32, pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=32, pady=(0, 16))

        campos = ctk.CTkFrame(scroll, fg_color="transparent")
        campos.pack(fill="x")
        campos.columnconfigure((0, 1), weight=1, uniform="col")

        def label(txt, row, col):
            ctk.CTkLabel(campos, text=txt, font=ctk.CTkFont(size=13), anchor="w"
                         ).grid(row=row*2, column=col, sticky="w", pady=(8, 0))

        def entry(row, col, placeholder=""):
            e = ctk.CTkEntry(campos, placeholder_text=placeholder, height=38)
            e.grid(row=row*2+1, column=col, sticky="ew",
                   padx=(0, 12) if col == 0 else (12, 0))
            return e

        label("Nome do Objeto *", 0, 0);  self.e_nome    = entry(0, 0, "Ex: Chave, Carteira…")
        label("Data Encontrada *", 0, 1); self.e_data    = entry(0, 1, "DD/MM/AAAA")
        self.e_data.insert(0, datetime.date.today().strftime("%d/%m/%Y"))
        aplicar_mascara_data(self.e_data)

        label("Local Encontrado", 1, 0);  self.e_local   = entry(1, 0, "Ex: Recepção, Bloco A…")
        label("Quem Encontrou",   1, 1);  self.e_quem    = entry(1, 1, "Nome do colaborador")
        label("Empresa",          2, 0);  self.e_empresa = entry(2, 0, "Nome da empresa")

        ctk.CTkLabel(campos, text="Descrição", font=ctk.CTkFont(size=13), anchor="w"
                     ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.e_descricao = ctk.CTkTextbox(campos, height=90)
        self.e_descricao.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=32, pady=(0, 24))
        ctk.CTkButton(bar, text="Cancelar", width=120, fg_color="transparent",
                      border_width=1, command=self._cancelar).pack(side="right", padx=(8, 0))
        ctk.CTkButton(bar, text="Salvar Objeto", width=160,
                      command=self._salvar).pack(side="right")

    def _salvar(self):
        import datetime as dt
        nome = self.e_nome.get().strip()
        data = self.e_data.get().strip()

        if not nome:
            messagebox.showwarning("Atenção", "O nome do objeto é obrigatório.")
            self.e_nome.focus(); return
        if not data:
            messagebox.showwarning("Atenção", "A data encontrada é obrigatória.")
            self.e_data.focus(); return
        try:
            dt.datetime.strptime(data, "%d/%m/%Y")
        except ValueError:
            messagebox.showwarning("Atenção", "Data inválida. Use o formato DD/MM/AAAA.")
            self.e_data.focus(); return

        dados = {
            "id":                  proximo_id_objeto(),
            "nome":                nome,
            "descricao":           self.e_descricao.get("1.0", "end").strip(),
            "data_encontrada":     data,
            "local_encontrado":    self.e_local.get().strip(),
            "quem_encontrou":      self.e_quem.get().strip(),
            "empresa":             self.e_empresa.get().strip(),
            "id_usuario_cadastro": self.usuario["id"],
            "_usuario":            self.usuario.get("nome", "sistema"),
        }
        inserir_objeto(dados)
        from views.lista_objetos_view import mostrar_toast
        mostrar_toast(self.winfo_toplevel(), f"Objeto '{nome}' cadastrado — ID {dados['id']}")
        if self.on_salvo:
            self.on_salvo()

    def _cancelar(self):
        if self.on_salvo:
            self.on_salvo()

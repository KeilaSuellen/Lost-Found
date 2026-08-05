import customtkinter as ctk
from tkinter import messagebox
import os, sys
from PIL import Image
from utils import resource_path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import listar_usuarios, inserir_usuario, deletar_usuario, alterar_senha

_BASE = resource_path("assets")


class UsuariosView(ctk.CTkFrame):

    def __init__(self, master, usuario: dict):
        super().__init__(master, fg_color="transparent")
        self.usuario_logado = usuario
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        # Título
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=32, pady=(24, 16))
        try:
            img = ctk.CTkImage(Image.open(resource_path(os.path.join("assets", "usuario.png"))), size=(32, 32))
            ctk.CTkLabel(topo, image=img, text="").pack(side="left", padx=(0, 10))
        except Exception:
            pass
        ctk.CTkLabel(topo, text="Gerenciar Usuários",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(expand=True, fill="both", padx=32, pady=(0, 24))

        # Lista
        painel_lista = ctk.CTkFrame(body)
        painel_lista.pack(side="left", expand=True, fill="both", padx=(0, 16))

        ctk.CTkLabel(painel_lista, text="Usuários cadastrados",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     ).pack(pady=(16, 4), padx=16, anchor="w")
        ctk.CTkLabel(painel_lista, text="Clique em 🔑 para alterar senha ou 🗑 para remover",
                     font=ctk.CTkFont(size=11), text_color="gray",
                     ).pack(pady=(0, 12), padx=16, anchor="w")

        # Header da lista
        h = ctk.CTkFrame(painel_lista, fg_color="#2b2b2b", corner_radius=8, height=38)
        h.pack(fill="x", padx=12, pady=(0, 4))
        h.pack_propagate(False)
        for txt, relx in [("Nome", 0.02), ("Nível", 0.52), ("Ações", 0.75)]:
            ctk.CTkLabel(h, text=txt, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#cccccc", anchor="w",
                         ).place(relx=relx, rely=0.5, anchor="w")

        self.scroll = ctk.CTkScrollableFrame(painel_lista, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=8, pady=(0, 12))

        # Formulário novo usuário 
        painel_form = ctk.CTkFrame(body, width=300)
        painel_form.pack(side="right", fill="y")
        painel_form.pack_propagate(False)

        ctk.CTkLabel(painel_form, text="Novo Usuário",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     ).pack(pady=(20, 4), padx=20, anchor="w")
        ctk.CTkLabel(painel_form, text="Preencha os dados do novo operador",
                     font=ctk.CTkFont(size=11), text_color="gray",
                     ).pack(pady=(0, 16), padx=20, anchor="w")

        def label(txt):
            ctk.CTkLabel(painel_form, text=txt, font=ctk.CTkFont(size=12),
                         anchor="w").pack(fill="x", padx=20, pady=(6, 0))

        label("Nome de usuário")
        self.e_nome = ctk.CTkEntry(painel_form, placeholder_text="Ex: joao.silva", height=38)
        self.e_nome.pack(fill="x", padx=20, pady=(2, 0))

        label("Senha")
        self.e_senha = ctk.CTkEntry(painel_form, placeholder_text="Mínimo 4 caracteres",
                                     show="•", height=38)
        self.e_senha.pack(fill="x", padx=20, pady=(2, 0))

        label("Nível de acesso")
        self.nivel_var = ctk.StringVar(value="Operador")
        ctk.CTkSegmentedButton(painel_form, values=["Operador", "Administrador"],
                               variable=self.nivel_var,
                               ).pack(fill="x", padx=20, pady=(4, 0))

        # Diferença visual entre os níveis
        self.lbl_nivel_info = ctk.CTkLabel(
            painel_form, text="Operador: cadastra e registra retiradas",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w")
        self.lbl_nivel_info.pack(fill="x", padx=20, pady=(4, 0))
        self.nivel_var.trace_add("write", self._atualizar_info_nivel)

        ctk.CTkFrame(painel_form, height=1, fg_color="gray30").pack(
            fill="x", padx=20, pady=16)

        ctk.CTkButton(painel_form, text="➕  Adicionar Usuário", height=42,
                      command=self._adicionar,
                      ).pack(fill="x", padx=20, pady=(0, 20))

    def _atualizar_info_nivel(self, *_):
        if self.nivel_var.get() == "Administrador":
            self.lbl_nivel_info.configure(text="Administrador: acesso total ao sistema")
        else:
            self.lbl_nivel_info.configure(text="Operador: cadastra e registra retiradas")

    def _carregar(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        usuarios = listar_usuarios()
        for i, u in enumerate(usuarios):
            self._linha_usuario(u, i)

    def _linha_usuario(self, u: dict, i: int):
        cor   = "#2a2a2a" if i % 2 == 0 else "#333333"
        linha = ctk.CTkFrame(self.scroll, fg_color=cor, corner_radius=6, height=48)
        linha.pack(fill="x", pady=2)
        linha.pack_propagate(False)

        # Nome
        ctk.CTkLabel(linha, text=u["nome"],
                     font=ctk.CTkFont(size=13, weight="bold"),
                     anchor="w",
                     ).place(relx=0.02, rely=0.5, anchor="w")

        # Nível com badge colorido
        cor_n = "#4caf50" if u["nivel"] == "Administrador" else "#2196f3"
        badge = ctk.CTkFrame(linha, fg_color=cor_n, corner_radius=4, width=100, height=24)
        badge.place(relx=0.52, rely=0.5, anchor="w")
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=u["nivel"], font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        # Botões
        acoes = ctk.CTkFrame(linha, fg_color="transparent")
        acoes.place(relx=0.75, rely=0.5, anchor="w")

        ctk.CTkButton(acoes, text="🔑", width=36, height=30,
                      font=ctk.CTkFont(size=14),
                      fg_color="#2a3a2a", hover_color="#1a2a1a",
                      command=lambda uid=u["id"], nome=u["nome"]: self._alterar_senha(uid, nome),
                      ).pack(side="left", padx=(0, 4))

        pode = u["id"] != self.usuario_logado["id"]
        ctk.CTkButton(acoes, text="🗑️", width=36, height=30,
                      font=ctk.CTkFont(size=14),
                      fg_color="#6e1a1a" if pode else "#3a3a3a",
                      hover_color="#5a1212" if pode else "#3a3a3a",
                      state="normal" if pode else "disabled",
                      command=lambda uid=u["id"], nome=u["nome"]: self._deletar(uid, nome),
                      ).pack(side="left")

    def _adicionar(self):
        nome  = self.e_nome.get().strip()
        senha = self.e_senha.get().strip()
        nivel = self.nivel_var.get()
        if not nome or not senha:
            messagebox.showwarning("Atenção", "Preencha nome e senha."); return
        if len(senha) < 4:
            messagebox.showwarning("Atenção", "A senha deve ter pelo menos 4 caracteres."); return
        try:
            inserir_usuario(nome, senha, nivel)
            messagebox.showinfo("Sucesso", f"Usuário '{nome}' criado!")
            self.e_nome.delete(0, "end")
            self.e_senha.delete(0, "end")
            self._carregar()
        except Exception as e:
            messagebox.showerror("Erro", f"Usuário já existe ou erro ao criar.\n{e}")

    def _alterar_senha(self, uid, nome):
        dialog = ctk.CTkInputDialog(text=f"Nova senha para '{nome}':", title="Alterar Senha")
        nova = dialog.get_input()
        if nova and nova.strip():
            if len(nova.strip()) < 4:
                messagebox.showwarning("Atenção", "Senha deve ter pelo menos 4 caracteres."); return
            alterar_senha(uid, nova.strip())
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")

    def _deletar(self, uid, nome):
        if messagebox.askyesno("Confirmar", f"Remover usuário '{nome}'?\nEsta ação não pode ser desfeita.",
                               icon="warning"):
            deletar_usuario(uid)
            self._carregar()

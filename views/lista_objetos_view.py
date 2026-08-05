import customtkinter as ctk
from tkinter import messagebox
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import (listar_objetos, atualizar_objeto, excluir_objeto,
                          desfazer_retirada, buscar_retirada_por_objeto,
                          atualizar_retirada, registrar_log)
from utils import aplicar_mascara_data, aplicar_mascara_documento

# Larguras fixas das colunas em pixels
COL_W = [100, 190, 200, 105, 125, 200]
COLS  = ["ID", "Nome", "Descrição", "Data", "Status", "Ações"]


def mostrar_toast(master, mensagem: str, cor: str = "#1D9E75", duracao_ms: int = 2500):
    """Exibe uma notificação flutuante no canto inferior direito."""
    toast = ctk.CTkFrame(master, fg_color=cor, corner_radius=10)
    ctk.CTkLabel(toast, text=mensagem, text_color="white",
                 font=ctk.CTkFont(size=13, weight="bold"),
                 padx=18, pady=10).pack()
    toast.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
    master.after(duracao_ms, toast.destroy)


class ListaObjetosView(ctk.CTkFrame):

    def __init__(self, master, usuario: dict, on_registrar_retirada=None, filtro_inicial="Todos"):
        super().__init__(master, fg_color="transparent")
        self.usuario               = usuario
        self.on_registrar_retirada = on_registrar_retirada
        self._objetos              = []
        self._filtro_inicial       = filtro_inicial
        self._pagina               = 0
        self._por_pagina           = 50
        self._resultado_filtrado   = []
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        # Título + filtro
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))

        titulo = ctk.CTkFrame(header, fg_color="transparent")
        titulo.pack(side="left")
        try:
            from PIL import Image
            img = ctk.CTkImage(Image.open(
                os.path.join(os.path.dirname(__file__), "..", "assets", "lista.png")), size=(28,28))
            ctk.CTkLabel(titulo, image=img, text="").pack(side="left", padx=(0,8))
        except Exception: pass
        ctk.CTkLabel(titulo, text="Objetos Registrados",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")

        self.filtro_var = ctk.StringVar(value=self._filtro_inicial)
        ctk.CTkSegmentedButton(header,
            values=["Todos", "Disponível", "Retirado", "Arquivado"],
            variable=self.filtro_var, command=self._filtrar, width=340,
        ).pack(side="right")

        # Busca
        self.e_busca = ctk.CTkEntry(self,
            placeholder_text="Buscar por ID, nome, descrição, local ou empresa…", height=38)
        self.e_busca.pack(fill="x", padx=24, pady=(0, 6))
        self.e_busca.bind("<KeyRelease>", lambda _: self._filtrar())
        self.e_busca.bind("<Escape>", lambda _: (self.e_busca.delete(0, "end"), self._filtrar()))

        # Header fixo externo ao scroll — usa mesmo padding lateral (padx=24)
        # Offset direito de 16px compensa a scrollbar interna do CTkScrollableFrame
        hdr = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=6, height=36)
        hdr.pack(fill="x", padx=24, pady=(0, 1))
        hdr.pack_propagate(False)
        # Colunas espelham COL_W; última coluna (Ações) recebe peso extra para absorver scrollbar
        col_weights = [0, 1, 1, 0, 0, 0]
        for i, (col, w) in enumerate(zip(COLS, COL_W)):
            hdr.columnconfigure(i, minsize=w, weight=col_weights[i])
            ctk.CTkLabel(hdr, text=col,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#aaaaaa", anchor="w",
                         ).grid(row=0, column=i, padx=(14, 4) if i == 0 else (8, 4), pady=0, sticky="w")

        # Área scrollável
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=24, pady=(0,4))
        for i, w in enumerate(COL_W):
            self.scroll.columnconfigure(i, minsize=w, weight=1 if i in (1,2) else 0)

        # Barra de paginação
        self._pag_bar = ctk.CTkFrame(self, fg_color="transparent")
        self._pag_bar.pack(fill="x", padx=24, pady=(2, 0))

        self._btn_ant = ctk.CTkButton(self._pag_bar, text="← Anterior", width=110,
                                       fg_color="transparent", border_width=1,
                                       command=self._pagina_anterior)
        self._btn_ant.pack(side="left")

        self._lbl_pagina = ctk.CTkLabel(self._pag_bar, text="",
                                         font=ctk.CTkFont(size=13), text_color="gray")
        self._lbl_pagina.pack(side="left", expand=True)

        self._btn_prox = ctk.CTkButton(self._pag_bar, text="Próximo →", width=110,
                                        fg_color="transparent", border_width=1,
                                        command=self._proxima_pagina)
        self._btn_prox.pack(side="right")

        self.lbl_total = ctk.CTkLabel(self, text="",
                                       font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_total.pack(pady=(2, 8))

    def _carregar(self):
        self._objetos = listar_objetos()
        self._filtrar()

    def _filtrar(self, *_):
        filtro = self.filtro_var.get()
        busca  = self.e_busca.get().strip().lower()
        result = self._objetos
        if filtro == "Disponível":
            result = [o for o in result if o["status"] == "disponivel"]
        elif filtro == "Retirado":
            result = [o for o in result if o["status"] == "retirado"]
        elif filtro == "Arquivado":
            result = [o for o in result if o["status"] == "arquivado"]
        if busca:
            result = [o for o in result if
                      busca in (o["id"] or "").lower() or
                      busca in (o["nome"] or "").lower() or
                      busca in (o["descricao"] or "").lower() or
                      busca in (o["local_encontrado"] or "").lower() or
                      busca in (o["empresa"] or "").lower()]
        self._resultado_filtrado = result
        self._pagina = 0
        self._renderizar_pagina()

    def _pagina_anterior(self):
        if self._pagina > 0:
            self._pagina -= 1
            self._renderizar_pagina()

    def _proxima_pagina(self):
        total_pags = max(1, -(-len(self._resultado_filtrado) // self._por_pagina))
        if self._pagina < total_pags - 1:
            self._pagina += 1
            self._renderizar_pagina()

    def _renderizar_pagina(self):
        inicio = self._pagina * self._por_pagina
        fim    = inicio + self._por_pagina
        pagina = self._resultado_filtrado[inicio:fim]
        total  = len(self._resultado_filtrado)
        total_pags = max(1, -(-total // self._por_pagina))

        # Atualiza botões e label de página
        self._btn_ant.configure(state="normal" if self._pagina > 0 else "disabled")
        self._btn_prox.configure(state="normal" if self._pagina < total_pags - 1 else "disabled")
        if total_pags > 1:
            self._lbl_pagina.configure(
                text=f"Página {self._pagina + 1} de {total_pags}")
            self._pag_bar.pack(fill="x", padx=24, pady=(2, 0))
        else:
            self._pag_bar.pack_forget()

        self._renderizar(pagina, total)

    def _renderizar(self, objetos, total_filtrado=None):
        for w in self.scroll.winfo_children():
            w.destroy()

        total = total_filtrado if total_filtrado is not None else len(objetos)

        if not objetos:
            ctk.CTkLabel(self.scroll, text="Nenhum objeto encontrado.",
                         text_color="gray", font=ctk.CTkFont(size=14)).grid(
                         row=0, column=0, columnspan=6, pady=40)
            self.lbl_total.configure(text="0 objetos")
            return

        for i, obj in enumerate(objetos):
            status  = obj["status"]
            cor_s   = {"disponivel": "#4caf50", "arquivado": "#e0a05c"}.get(status, "#e05c5c")
            label_s = {"disponivel": "Disponível", "arquivado": "Arquivado"}.get(status, "Retirado")
            borda   = {"disponivel": "#1D9E75", "arquivado": "#EF9F27"}.get(status, "#E24B4A")

            linha = ctk.CTkFrame(self.scroll, fg_color="#1e1e1e", corner_radius=0, height=44)
            linha.grid(row=i, column=0, columnspan=6, sticky="ew", pady=1)
            linha.pack_propagate(False)
            for j, w in enumerate(COL_W):
                linha.columnconfigure(j, minsize=w, weight=1 if j in (1,2) else 0)

            barra = ctk.CTkFrame(linha, fg_color=borda, width=4, corner_radius=0)
            barra.place(x=0, y=0, relheight=1)

            vals = [
                obj["id"],
                obj["nome"] or "-",
                obj["descricao"] or "-",
                (obj["data_encontrada"] or "")[:10],
            ]
            for j, val in enumerate(vals):
                ctk.CTkLabel(linha, text=val,
                             font=ctk.CTkFont(size=13),
                             anchor="w", text_color="white",
                             ).grid(row=0, column=j, padx=(16,4) if j==0 else (8,4), pady=0, sticky="w")

            ctk.CTkLabel(linha, text=label_s,
                         font=ctk.CTkFont(size=13),
                         text_color=cor_s, anchor="w",
                         ).grid(row=0, column=4, padx=(8,4), pady=0, sticky="w")

            acoes = ctk.CTkFrame(linha, fg_color="transparent")
            acoes.grid(row=0, column=5, padx=(4,8), pady=4, sticky="w")

            if status == "disponivel":
                ctk.CTkButton(acoes, text="Retirar", width=34, height=30,
                    font=ctk.CTkFont(size=14),
                    fg_color="#1D9E75", hover_color="#0F6E56",
                    command=lambda o=obj: self._abrir_retirada(o),
                ).pack(side="left", padx=(0,3))

            if status == "retirado":
                ctk.CTkButton(acoes, text="Desfazer", width=34, height=30,
                    font=ctk.CTkFont(size=14),
                    fg_color="#444441", hover_color="#2C2C2A",
                    command=lambda o=obj: self._confirmar_desfazer(o),
                ).pack(side="left", padx=(0,3))

            if status == "retirado":
                ctk.CTkButton(acoes, text="Editar", width=34, height=30,
                    font=ctk.CTkFont(size=14),
                    fg_color="#444441", hover_color="#2C2C2A",
                    command=lambda o=obj: self._editar_retirada(o),
                ).pack(side="left", padx=(0,3))
            else:
                ctk.CTkButton(acoes, text="Editar", width=34, height=30,
                    font=ctk.CTkFont(size=14),
                    fg_color="#444441", hover_color="#2C2C2A",
                    command=lambda o=obj: self._abrir_edicao(o),
                ).pack(side="left", padx=(0,3))

            ctk.CTkButton(acoes, text="Excluir", width=34, height=30,
                font=ctk.CTkFont(size=14),
                fg_color="#A32D2D", hover_color="#791F1F",
                command=lambda o=obj: self._confirmar_excluir(o),
            ).pack(side="left")

        disp = sum(1 for o in self._resultado_filtrado if o["status"] == "disponivel")
        inicio = self._pagina * self._por_pagina + 1
        fim    = min(inicio + len(objetos) - 1, total)
        pag_info = f"  •  exibindo {inicio}–{fim}" if total > self._por_pagina else ""
        self.lbl_total.configure(
            text=f"{total} objeto(s)  •  {disp} disponível(is){pag_info}")

    def _confirmar_excluir(self, obj):
        if not messagebox.askyesno("Excluir objeto",
            f"Tem certeza que deseja excluir '{obj['nome']}' (ID {obj['id']})?\n\nEsta ação não pode ser desfeita.\nO histórico de retiradas vinculado também será removido.",
            icon="warning"): return
        try:
            excluir_objeto(obj["id"], self.usuario.get("nome","sistema"))
            mostrar_toast(self, f"Objeto {obj['id']} excluído", cor="#A32D2D")
        except Exception as e:
            messagebox.showerror("Erro ao excluir", str(e))
        finally:
            self._carregar()

    def _confirmar_desfazer(self, obj):
        if messagebox.askyesno("Desfazer retirada",
            f"Desfazer a retirada de '{obj['nome']}' (ID {obj['id']})?\n\nO objeto voltará para 'Disponível'.",
            icon="warning"):
            desfazer_retirada(obj["id"], self.usuario.get("nome","sistema"))
            mostrar_toast(self, f"Retirada desfeita — {obj['id']}")
            self._carregar()

    def _editar_retirada(self, obj):
        ret = buscar_retirada_por_objeto(obj["id"])
        if not ret:
            messagebox.showwarning("Atenção", "Nenhuma retirada encontrada para este objeto.")
            return
        EdicaoRetiradaDialog(self, obj, ret, usuario=self.usuario, on_salvo=self._on_salvo_com_toast)

    def _abrir_retirada(self, obj):
        if self.on_registrar_retirada:
            self.on_registrar_retirada(obj)

    def _abrir_edicao(self, obj):
        EdicaoObjetoDialog(self, obj, usuario=self.usuario, on_salvo=self._on_salvo_com_toast)

    def _on_salvo_com_toast(self, msg="Salvo com sucesso!"):
        pagina_atual = self._pagina
        mostrar_toast(self, msg)
        self._carregar()
        # Tenta manter a mesma página se ainda existir
        total_pags = max(1, -(-len(self._resultado_filtrado) // self._por_pagina))
        self._pagina = min(pagina_atual, total_pags - 1)
        self._renderizar_pagina()

    def atualizar(self):
        self._carregar()


class EdicaoObjetoDialog(ctk.CTkToplevel):

    def __init__(self, master, obj: dict, usuario: dict = None, on_salvo=None):
        super().__init__(master)
        self.obj      = obj
        self.usuario  = usuario or {}
        self.on_salvo = on_salvo
        self.title(f"Editar Objeto — {obj['id']}")
        self.geometry("520x480")
        self.resizable(False, False)
        self.grab_set(); self.focus_set()
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text=f"Editar  {self.obj['id']}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     ).pack(pady=(20,4), padx=24, anchor="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=24, pady=(0,8))

        def lbl(txt):
            ctk.CTkLabel(scroll, text=txt, font=ctk.CTkFont(size=13),
                         anchor="w").pack(anchor="w", pady=(8,0))

        def ent(valor=""):
            e = ctk.CTkEntry(scroll, height=36)
            e.pack(fill="x")
            if valor: e.insert(0, valor)
            return e

        lbl("Nome do Objeto *");   self.e_nome    = ent(self.obj.get("nome",""))
        lbl("Data Encontrada");    self.e_data    = ent(self.obj.get("data_encontrada",""))
        aplicar_mascara_data(self.e_data)
        lbl("Local Encontrado");   self.e_local   = ent(self.obj.get("local_encontrado",""))
        lbl("Quem Encontrou");     self.e_quem    = ent(self.obj.get("quem_encontrou",""))
        lbl("Empresa");            self.e_empresa = ent(self.obj.get("empresa",""))
        lbl("Descrição")
        self.e_desc = ctk.CTkTextbox(scroll, height=80)
        self.e_desc.pack(fill="x")
        self.e_desc.insert("1.0", self.obj.get("descricao","") or "")

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(0,20))
        ctk.CTkButton(bar, text="Cancelar", width=110, fg_color="transparent",
                      border_width=1, command=self.destroy).pack(side="right", padx=(8,0))
        ctk.CTkButton(bar, text="Salvar", width=120,
                      command=self._salvar).pack(side="right")

    def _salvar(self):
        import datetime
        nome = self.e_nome.get().strip()
        data = self.e_data.get().strip()
        if not nome:
            messagebox.showwarning("Atenção","O nome é obrigatório.", parent=self); return
        if data:
            try: datetime.datetime.strptime(data, "%d/%m/%Y")
            except ValueError:
                messagebox.showwarning("Atenção","Data inválida. Use DD/MM/AAAA.", parent=self)
                self.e_data.focus(); return
        dados = {
            "nome":             nome,
            "descricao":        self.e_desc.get("1.0","end").strip(),
            "data_encontrada":  data,
            "local_encontrado": self.e_local.get().strip(),
            "quem_encontrou":   self.e_quem.get().strip(),
            "empresa":          self.e_empresa.get().strip(),
            "_usuario":         self.usuario.get("nome","sistema"),
        }
        atualizar_objeto(self.obj["id"], dados)
        self.destroy()
        if self.on_salvo:
            self.on_salvo(f"Objeto {self.obj['id']} atualizado!")


class EdicaoRetiradaDialog(ctk.CTkToplevel):

    def __init__(self, master, obj: dict, retirada: dict, usuario: dict = None, on_salvo=None):
        super().__init__(master)
        self.obj      = obj
        self.retirada = retirada
        self.usuario  = usuario or {}
        self.on_salvo = on_salvo
        self.title(f"Editar Retirada — {obj['id']}")
        self.geometry("480x400")
        self.resizable(False, False)
        self.grab_set(); self.focus_set()
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text=f"Editar Retirada — {self.obj['id']}",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     ).pack(pady=(20, 2), padx=24, anchor="w")
        ctk.CTkLabel(self, text=f"Objeto: {self.obj.get('nome', '')}",
                     font=ctk.CTkFont(size=12), text_color="gray",
                     ).pack(pady=(0, 12), padx=24, anchor="w")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=24, pady=(0, 8))

        def lbl(txt):
            ctk.CTkLabel(scroll, text=txt, font=ctk.CTkFont(size=13),
                         anchor="w").pack(anchor="w", pady=(8, 0))

        def ent(valor=""):
            e = ctk.CTkEntry(scroll, height=36)
            e.pack(fill="x")
            if valor: e.insert(0, valor)
            return e

        lbl("Nome do Retirante *"); self.e_nome    = ent(self.retirada.get("nome_retirante",""))
        lbl("Documento (RG/CPF)");  self.e_doc     = ent(self.retirada.get("documento",""))
        aplicar_mascara_documento(self.e_doc)
        lbl("Empresa");             self.e_empresa = ent(self.retirada.get("empresa",""))
        lbl("Data de Retirada *");  self.e_data    = ent(self.retirada.get("data_retirada",""))
        aplicar_mascara_data(self.e_data)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(bar, text="Cancelar", width=110, fg_color="transparent",
                      border_width=1, command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(bar, text="Salvar", width=120,
                      command=self._salvar).pack(side="right")

    def _salvar(self):
        import datetime
        nome = self.e_nome.get().strip()
        data = self.e_data.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "O nome do retirante é obrigatório.", parent=self); return
        if data:
            try: datetime.datetime.strptime(data, "%d/%m/%Y")
            except ValueError:
                messagebox.showwarning("Atenção", "Data inválida. Use DD/MM/AAAA.", parent=self)
                self.e_data.focus(); return
        atualizar_retirada(self.retirada["id"], {
            "nome_retirante": nome,
            "documento":      self.e_doc.get().strip(),
            "empresa":        self.e_empresa.get().strip(),
            "data_retirada":  data,
        })
        registrar_log(self.usuario.get("nome","sistema"), "Editou retirada",
                      self.obj["id"], nome)
        self.destroy()
        if self.on_salvo:
            self.on_salvo(f"Retirada de {self.obj['id']} atualizada!")

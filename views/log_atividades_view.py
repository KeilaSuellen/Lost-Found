import customtkinter as ctk
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import listar_log

COLS  = ["Data/Hora", "Usuário", "Ação", "ID Objeto", "Detalhe"]
COL_W = [145, 110, 160, 100, 220]

CORES_ACAO = {
    "Cadastrou objeto":   "#1D9E75",
    "Editou objeto":      "#5B8DEF",
    "Registrou retirada": "#E0A05C",
    "Desfez retirada":    "#C97BDB",
    "Excluiu objeto":     "#E24B4A",
    "Editou retirada":    "#5B8DEF",
}


class LogAtividadesView(ctk.CTkFrame):

    def __init__(self, master, usuario: dict):
        super().__init__(master, fg_color="transparent")
        self.usuario = usuario
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(header, text="Log de Atividades",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Atualizar", width=110,
                      command=self._carregar).pack(side="right")

        # Busca
        self.e_busca = ctk.CTkEntry(self,
            placeholder_text="Filtrar por usuário, ação ou ID…", height=38)
        self.e_busca.pack(fill="x", padx=24, pady=(0, 6))
        self.e_busca.bind("<KeyRelease>", lambda _: self._filtrar())
        self.e_busca.bind("<Escape>", lambda _: (self.e_busca.delete(0, "end"), self._filtrar()))

        # Header fixo externo ao scroll
        hdr = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=6, height=36)
        hdr.pack(fill="x", padx=24, pady=(0, 1))
        hdr.pack_propagate(False)
        for i, (col, w) in enumerate(zip(COLS, COL_W)):
            hdr.columnconfigure(i, minsize=w, weight=1 if i == 4 else 0)
            ctk.CTkLabel(hdr, text=col,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#aaaaaa", anchor="w",
                         ).grid(row=0, column=i, padx=(14, 4) if i == 0 else (8, 4), pady=0, sticky="w")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=24, pady=(0, 4))
        for i, w in enumerate(COL_W):
            self.scroll.columnconfigure(i, minsize=w, weight=1 if i == 4 else 0)

        self.lbl_total = ctk.CTkLabel(self, text="",
                                       font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_total.pack(pady=(0, 8))

    def _carregar(self):
        self._logs = listar_log(200)
        self._filtrar()

    def _filtrar(self, *_):
        busca = self.e_busca.get().strip().lower()
        result = self._logs
        if busca:
            result = [l for l in result if
                      busca in (l["usuario"] or "").lower() or
                      busca in (l["acao"] or "").lower() or
                      busca in (l["id_objeto"] or "").lower() or
                      busca in (l["detalhe"] or "").lower()]
        self._renderizar(result)

    def _renderizar(self, logs):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not logs:
            ctk.CTkLabel(self.scroll, text="Nenhuma atividade registrada.",
                         text_color="gray", font=ctk.CTkFont(size=14)
                         ).grid(row=0, column=0, columnspan=5, pady=40)
            self.lbl_total.configure(text="0 registros")
            return

        for i, log in enumerate(logs):
            cor_acao = CORES_ACAO.get(log["acao"], "#aaaaaa")
            bg = "#1e1e1e" if i % 2 == 0 else "#242424"

            linha = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=0, height=38)
            linha.grid(row=i, column=0, columnspan=5, sticky="ew", pady=0)
            linha.pack_propagate(False)
            for j, w in enumerate(COL_W):
                linha.columnconfigure(j, minsize=w, weight=1 if j == 4 else 0)

            # Barra colorida por tipo de ação
            ctk.CTkFrame(linha, fg_color=cor_acao, width=4,
                         corner_radius=0).place(x=0, y=0, relheight=1)

            vals = [
                log["data_hora"] or "",
                log["usuario"] or "",
                log["acao"] or "",
                log["id_objeto"] or "-",
                log["detalhe"] or "-",
            ]
            for j, val in enumerate(vals):
                cor_txt = cor_acao if j == 2 else "white"
                ctk.CTkLabel(linha, text=val,
                             font=ctk.CTkFont(size=12),
                             anchor="w", text_color=cor_txt,
                             ).grid(row=0, column=j,
                                    padx=(16, 4) if j == 0 else (8, 4),
                                    pady=0, sticky="w")

        self.lbl_total.configure(text=f"{len(logs)} registro(s)")

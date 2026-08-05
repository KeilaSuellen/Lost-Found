import customtkinter as ctk
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import listar_retiradas

COL_W = [100, 140, 180, 120, 130, 110]
COLS  = ["ID Objeto", "Objeto", "Retirante", "Documento", "Empresa", "Data Retirada"]


class HistoricoRetiradasView(ctk.CTkFrame):

    def __init__(self, master, usuario: dict):
        super().__init__(master, fg_color="transparent")
        self.usuario    = usuario
        self._retiradas = []
        self._build_ui()
        self._carregar()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=24, pady=(20,10))
        try:
            from PIL import Image
            img = ctk.CTkImage(Image.open(
                os.path.join(os.path.dirname(__file__), "..", "assets", "retirada.png")), size=(28,28))
            ctk.CTkLabel(topo, image=img, text="").pack(side="left", padx=(0,8))
        except Exception: pass
        ctk.CTkLabel(topo, text="Histórico de Retiradas",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")

        self.e_busca = ctk.CTkEntry(self,
            placeholder_text="Buscar por nome, objeto ou documento…", height=38)
        self.e_busca.pack(fill="x", padx=24, pady=(0,6))
        self.e_busca.bind("<KeyRelease>", lambda _: self._filtrar())

        # Header fixo
        hdr = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8, height=40)
        hdr.pack(fill="x", padx=24, pady=(0,2))
        hdr.pack_propagate(False)
        for i, (col, w) in enumerate(zip(COLS, COL_W)):
            hdr.columnconfigure(i, minsize=w, weight=1 if i in (1,2) else 0)
            ctk.CTkLabel(hdr, text=col,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="#cccccc", anchor="w",
                         ).grid(row=0, column=i, padx=(12,4), pady=8, sticky="w")

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=24, pady=(0,4))
        for i, w in enumerate(COL_W):
            self.scroll.columnconfigure(i, minsize=w, weight=1 if i in (1,2) else 0)

        self.lbl_total = ctk.CTkLabel(self, text="",
                                       font=ctk.CTkFont(size=13), text_color="gray")
        self.lbl_total.pack(pady=(0,8))

    def _carregar(self):
        self._retiradas = listar_retiradas()
        self._filtrar()

    def _filtrar(self, *_):
        busca  = self.e_busca.get().strip().lower()
        result = self._retiradas
        if busca:
            result = [r for r in result if
                      busca in (r["nome_retirante"] or "").lower() or
                      busca in (r["nome_objeto"]    or "").lower() or
                      busca in (r["documento"]      or "").lower() or
                      busca in (r["empresa"]        or "").lower()]
        self._renderizar(result)

    def _renderizar(self, retiradas):
        for w in self.scroll.winfo_children():
            w.destroy()

        if not retiradas:
            ctk.CTkLabel(self.scroll, text="Nenhuma retirada encontrada.",
                         text_color="gray", font=ctk.CTkFont(size=14)).grid(
                         row=0, column=0, columnspan=6, pady=40)
            self.lbl_total.configure(text="0 retiradas")
            return

        for i, r in enumerate(retiradas):
            cor   = "#2a2a2a" if i % 2 == 0 else "#333333"
            linha = ctk.CTkFrame(self.scroll, fg_color=cor, corner_radius=6, height=44)
            linha.grid(row=i, column=0, columnspan=6, sticky="ew", pady=2)
            linha.pack_propagate(False)
            for j, w in enumerate(COL_W):
                linha.columnconfigure(j, minsize=w, weight=1 if j in (1,2) else 0)

            vals = [
                r["id_objeto"],
                r["nome_objeto"]    or "-",
                r["nome_retirante"] or "-",
                r["documento"]      or "-",
                r["empresa"]        or "-",
                (r["data_retirada"] or "")[:10],
            ]
            for j, val in enumerate(vals):
                ctk.CTkLabel(linha, text=val,
                             font=ctk.CTkFont(size=13),
                             anchor="w", text_color="white",
                             ).grid(row=0, column=j, padx=(12,4), pady=0, sticky="w")

        self.lbl_total.configure(text=f"{len(retiradas)} retirada(s) registrada(s)")

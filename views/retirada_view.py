import customtkinter as ctk
from tkinter import messagebox
import datetime, os, sys, webbrowser, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.db import registrar_retirada
from utils import aplicar_mascara_data, aplicar_mascara_documento


class RetiradaView(ctk.CTkFrame):
    """Formulário para registrar a retirada de um objeto."""

    def __init__(self, master, usuario: dict, objeto: dict, on_concluido=None):
        super().__init__(master, fg_color="transparent")
        self.usuario      = usuario
        self.objeto       = objeto
        self.on_concluido = on_concluido
        self._build_ui()

    def _build_ui(self):
        self.pack(expand=True, fill="both")

        ctk.CTkLabel(self, text="Registrar Retirada",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     ).pack(pady=(24, 4), anchor="w", padx=32)

        # Card do objeto
        card = ctk.CTkFrame(self, corner_radius=10)
        card.pack(fill="x", padx=32, pady=(0, 20))
        ctk.CTkLabel(card, text="Objeto sendo retirado",
                     font=ctk.CTkFont(size=11), text_color="gray",
                     ).pack(anchor="w", padx=16, pady=(12, 0))
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=16, pady=(4, 12))
        for label, valor in [
            ("ID",    self.objeto["id"]),
            ("Nome",  self.objeto["nome"]),
            ("Local", self.objeto.get("local_encontrado") or "-"),
            ("Data",  (self.objeto.get("data_encontrada") or "")[:10]),
        ]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(anchor="w")
            ctk.CTkLabel(row, text=f"{label}:", font=ctk.CTkFont(size=12),
                         text_color="gray", width=50).pack(side="left")
            ctk.CTkLabel(row, text=valor, font=ctk.CTkFont(size=12, weight="bold"),
                         ).pack(side="left", padx=4)

        # Formulário
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=32)
        form.columnconfigure((0, 1), weight=1, uniform="col")

        def lbl(txt, row, col):
            ctk.CTkLabel(form, text=txt, font=ctk.CTkFont(size=13), anchor="w"
                         ).grid(row=row*2, column=col, sticky="w", pady=(8, 0))

        def ent(row, col, ph=""):
            e = ctk.CTkEntry(form, placeholder_text=ph, height=38)
            e.grid(row=row*2+1, column=col, sticky="ew",
                   padx=(0, 12) if col == 0 else (12, 0))
            return e

        lbl("Nome do Retirante *", 0, 0); self.e_nome    = ent(0, 0, "Nome completo")
        lbl("Documento (RG/CPF)",  0, 1); self.e_doc     = ent(0, 1, "Ex: 12.345.678-9")
        lbl("Empresa",             1, 0); self.e_empresa = ent(1, 0, "Nome da empresa")
        lbl("Data de Retirada *",  1, 1); self.e_data    = ent(1, 1, "DD/MM/AAAA")
        self.e_data.insert(0, datetime.date.today().strftime("%d/%m/%Y"))
        aplicar_mascara_data(self.e_data)
        aplicar_mascara_documento(self.e_doc)

        # Botões
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=32, pady=24)
        ctk.CTkButton(bar, text="Cancelar", width=120, fg_color="transparent",
                      border_width=1, command=self._cancelar).pack(side="right", padx=(8, 0))
        ctk.CTkButton(bar, text="Confirmar Retirada", width=180,
                      command=self._confirmar).pack(side="right")
        ctk.CTkButton(bar, text="Imprimir Formulário", width=180,
                      fg_color="#555", hover_color="#444",
                      command=self._imprimir_formulario).pack(side="left")

    def _confirmar(self):
        nome = self.e_nome.get().strip()
        data = self.e_data.get().strip()
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome do retirante."); return
        if not data:
            messagebox.showwarning("Atenção", "Informe a data de retirada."); return
        if not messagebox.askyesno("Confirmar",
                f"Confirmar retirada de '{self.objeto['nome']}' por {nome}?"):
            return
        dados = {
            "id_objeto":           self.objeto["id"],
            "nome_retirante":      nome,
            "documento":           self.e_doc.get().strip(),
            "empresa":             self.e_empresa.get().strip(),
            "data_retirada":       data,
            "id_usuario_retirada": self.usuario["id"],
            "_usuario":            self.usuario.get("nome", "sistema"),
        }
        registrar_retirada(dados)
        messagebox.showinfo("Sucesso", "Retirada registrada com sucesso!")
        if self.on_concluido:
            self.on_concluido()

    def _imprimir_formulario(self):
        obj      = self.objeto
        operador = self.usuario.get("nome", "")
        dias_pt  = {"Monday":"segunda-feira","Tuesday":"terça-feira","Wednesday":"quarta-feira",
                    "Thursday":"quinta-feira","Friday":"sexta-feira","Saturday":"sábado","Sunday":"domingo"}
        meses_pt = {"January":"janeiro","February":"fevereiro","March":"março","April":"abril",
                    "May":"maio","June":"junho","July":"julho","August":"agosto",
                    "September":"setembro","October":"outubro","November":"novembro","December":"dezembro"}
        d = datetime.date.today()
        dia_extenso = f"São Paulo, {dias_pt[d.strftime('%A')]}, {d.day} de {meses_pt[d.strftime('%B')]} de {d.year}"

        nome_obj      = obj.get("nome") or "-"
        descricao     = obj.get("descricao") or "-"
        local         = obj.get("local_encontrado") or "-"
        data_enc      = (obj.get("data_encontrada") or "")[:10]
        obj_id        = obj["id"]

        # Dados já preenchidos no formulário (se houver)
        ret_nome      = self.e_nome.get().strip()
        ret_doc       = self.e_doc.get().strip()
        ret_empresa   = self.e_empresa.get().strip()

  
        try:
            from database.db import obter_config
            from utils import logo_padrao_b64
            logo_b64 = obter_config("logo_b64", "")
            if not logo_b64:
                logo_b64 = logo_padrao_b64()
            nome_empresa = obter_config("nome_empresa", "CBRE · EZ Towers")
            site         = obter_config("site", "São Paulo, SP")
        except Exception:
            logo_b64     = ""
            nome_empresa = "CBRE · EZ Towers"
            site         = "São Paulo, SP"

        # Classe CSS: preenchido = fundo cinza, vazio = linha em branco
        cls_nome    = "" if ret_nome    else "empty"
        cls_doc     = "" if ret_doc     else "empty"
        cls_empresa = "" if ret_empresa else "empty"

        html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8">
<title>Formulário de Retirada — {obj_id}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box;}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f5f5f3;display:flex;justify-content:center;padding:32px 16px 48px;}}
  .page{{background:white;width:780px;padding:40px 48px;border-radius:4px;box-shadow:0 1px 8px rgba(0,0,0,0.08);}}
  .header{{display:flex;align-items:flex-start;justify-content:space-between;padding-bottom:20px;border-bottom:2px solid #1a1a1a;margin-bottom:28px;}}
  .logo-vs img{{height:48px;width:auto;}}
  .header-center{{text-align:center;}}
  .header-center .doc-title{{font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#1a1a1a;}}
  .header-center .doc-sub{{font-size:11px;color:#888;margin-top:3px;letter-spacing:0.5px;}}
  .header-right{{text-align:right;line-height:1.4;}}
  .header-right .client{{font-size:13px;font-weight:700;color:#1a1a1a;letter-spacing:0.5px;}}
  .header-right .site{{font-size:11px;color:#888;}}
  .section-label{{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#888;margin-bottom:12px;display:flex;align-items:center;gap:8px;}}
  .section-label::after{{content:'';flex:1;height:1px;background:#e8e8e6;}}
  .field{{margin-bottom:14px;}}
  .field-label{{font-size:10px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:#999;margin-bottom:5px;}}
  .field-value{{font-size:13px;color:#1a1a1a;padding:9px 12px;background:#f8f8f6;border:1px solid #e0e0dc;border-radius:2px;min-height:36px;line-height:1.4;}}
  .field-value.empty{{background:white;border-bottom:1.5px solid #1a1a1a;border-top:none;border-left:none;border-right:none;border-radius:0;min-height:40px;}}
  .field-value.tall{{min-height:58px;}}
  .two-col{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}}
  .two-col-3{{display:grid;grid-template-columns:160px 1fr;gap:14px;margin-bottom:14px;}}
  .separator{{height:1px;background:#e8e8e6;margin:22px 0;}}
  .declaration{{border:1px solid #ccc;padding:14px 18px;margin:22px 0;display:flex;gap:14px;align-items:flex-start;}}
  .declaration-icon{{flex-shrink:0;margin-top:1px;}}
  .declaration-text{{font-size:12px;color:#444;line-height:1.6;}}
  .declaration-text .highlight{{font-weight:600;color:#1a1a1a;}}
  .signatures{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:8px;}}
  .sig-label{{font-size:10px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:#999;margin-bottom:10px;}}
  .sig-area{{height:52px;border-bottom:1px solid #1a1a1a;margin-bottom:6px;}}
  .sig-name{{font-size:11px;color:#555;font-weight:600;}}
  .sig-hint{{font-size:10px;color:#aaa;}}
  .footer{{display:flex;justify-content:space-between;align-items:center;margin-top:28px;padding-top:16px;border-top:1px solid #e8e8e6;}}
  .footer-date{{font-size:11px;color:#aaa;}}
  .footer-proto{{font-size:10px;color:#bbb;font-weight:600;letter-spacing:1px;}}
  .no-print{{text-align:center;margin-top:28px;}}
  .btn-print{{padding:10px 36px;font-size:13px;cursor:pointer;background:#1a1a1a;color:white;border:none;border-radius:2px;font-weight:600;letter-spacing:1px;text-transform:uppercase;}}
  @media print{{body{{background:white;padding:0;}}.page{{box-shadow:none;width:100%;padding:24px 32px;}}.no-print{{display:none!important;}}}}
</style></head><body>
<div class="page">
  <div class="header">
    <div class="logo-vs"><img src="data:image/png;base64,{logo_b64}" alt="Verzani &amp; Sandrini"></div>
    <div class="header-center">
      <div class="doc-title">Formulário de Retirada</div>
      <div class="doc-sub">Achados e Perdidos / Lost &amp; Found</div>
    </div>
    <div class="header-right">
      <div class="client">{nome_empresa}</div>
      <div class="site">{site}</div>
    </div>
  </div>

  <div class="section-label">Identificação do Objeto / Item Identification</div>
  <div class="two-col-3">
    <div><div class="field-label">ID do Objeto</div><div class="field-value">{obj_id}</div></div>
    <div><div class="field-label">Data Encontrada / Date Found</div><div class="field-value">{data_enc}</div></div>
  </div>
  <div class="field"><div class="field-label">Nome / Item Name</div><div class="field-value">{nome_obj}</div></div>
  <div class="field"><div class="field-label">Descrição / Description</div><div class="field-value tall">{descricao}</div></div>
  <div class="field"><div class="field-label">Local Encontrado / Found Location</div><div class="field-value">{local}</div></div>

  <div class="separator"></div>

  <div class="section-label">Dados do Retirante / Recipient Information</div>
  <div class="field"><div class="field-label">Nome Completo / Full Name</div><div class="field-value {cls_nome}">{ret_nome}</div></div>
  <div class="two-col">
    <div><div class="field-label">Documento de Identidade / ID Number</div><div class="field-value {cls_doc}">{ret_doc}</div></div>
    <div><div class="field-label">Empresa / Company</div><div class="field-value {cls_empresa}">{ret_empresa}</div></div>
  </div>


  <div class="declaration">
    <svg class="declaration-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
      <path d="M12 2L3 6v6c0 5.25 3.75 10.15 9 11.25C17.25 22.15 21 17.25 21 12V6L12 2z" stroke="#1a1a1a" stroke-width="1.5" fill="none"/>
      <polyline points="9,12 11,14 15,10" stroke="#1a1a1a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div class="declaration-text">
      Declaro que recebi o objeto de <span class="highlight">ID {obj_id}</span> descrito acima, em bom estado de conservação.<br>
      <span style="color:#aaa;font-size:11px;margin-top:4px;display:block;">I hereby confirm receipt of the item described above in good condition.</span>
    </div>
  </div>

  <div class="signatures">
    <div class="sig-box">
      <div class="sig-label">Assinatura do Retirante / Recipient Signature</div>
      <div class="sig-area"></div>
      <div class="sig-hint">Assinatura / Signature</div>
    </div>
    <div class="sig-box">
      <div class="sig-label">Assinatura do Operador / Operator Signature</div>
      <div class="sig-area"></div>
      <div class="sig-name">{operador}</div>
      <div class="sig-hint">Operador responsável / Responsible operator</div>
    </div>
  </div>

  <div class="footer">
    <div class="footer-date">{dia_extenso}</div>
    <div class="footer-proto">PROTOCOLO · {obj_id}</div>
  </div>
  <div class="no-print">
    <button class="btn-print" onclick="window.print()">Imprimir</button>
  </div>
</div></body></html>"""

        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".html",
            prefix=f"formulario_{obj_id.replace('/', '_')}_",
            mode="w", encoding="utf-8")
        tmp.write(html); tmp.close()
        webbrowser.open(f"file:///{tmp.name}")

    def _cancelar(self):
        if self.on_concluido:
            self.on_concluido()

import sys, os


# ---------------------------------------------------------------------------
# Máscaras de entrada — funcionam com CTkEntry
# ---------------------------------------------------------------------------

def aplicar_mascara_data(entry) -> None:
    """
    Máscara DD/MM/AAAA robusta.
    Funciona corretamente ao digitar E ao apagar (tecla Delete/Backspace).
    """
    _ignorar = [False]

    def _formatar(d: str) -> str:
        d = d[:8]
        if len(d) > 4:
            return d[:2] + "/" + d[2:4] + "/" + d[4:]
        if len(d) > 2:
            return d[:2] + "/" + d[2:]
        return d

    def on_key(event):
        if _ignorar[0]:
            return
        # Ignora teclas de navegação e controle
        if event.keysym in ("Left", "Right", "Home", "End", "Tab",
                            "Shift_L", "Shift_R", "Control_L", "Control_R",
                            "Alt_L", "Alt_R", "Return", "Escape"):
            return

        _ignorar[0] = True
        raw    = entry.get()
        cursor = entry.index("insert")

        # Extrai só dígitos e conta quantos havia antes do cursor
        digits_before = "".join(c for c in raw[:cursor] if c.isdigit())
        digits_all    = "".join(c for c in raw if c.isdigit())

        formatted = _formatar(digits_all)

        entry.delete(0, "end")
        entry.insert(0, formatted)

        # Reposiciona cursor: conta os mesmos dígitos na string formatada
        count = 0
        new_pos = len(formatted)
        for i, ch in enumerate(formatted):
            if count == len(digits_before):
                new_pos = i
                break
            if ch.isdigit():
                count += 1

        entry.icursor(new_pos)
        _ignorar[0] = False

    entry.bind("<KeyRelease>", on_key)


def aplicar_mascara_cpf(entry) -> None:
    """
    Máscara CPF: 000.000.000-00
    """
    _ignorar = [False]

    def _formatar(d: str) -> str:
        d = d[:11]
        if len(d) > 9:
            return d[:3] + "." + d[3:6] + "." + d[6:9] + "-" + d[9:]
        if len(d) > 6:
            return d[:3] + "." + d[3:6] + "." + d[6:]
        if len(d) > 3:
            return d[:3] + "." + d[3:]
        return d

    def on_change(*_):
        if _ignorar[0]:
            return
        raw = entry.get()
        digits = "".join(c for c in raw if c.isdigit())
        formatted = _formatar(digits)
        if formatted != raw:
            _ignorar[0] = True
            entry.delete(0, "end")
            entry.insert(0, formatted)
            entry.icursor(len(formatted))
            _ignorar[0] = False

    entry.bind("<KeyRelease>", on_change)


def aplicar_mascara_rg(entry) -> None:
    """
    Máscara RG: 00.000.000-0  (formato SP — 9 dígitos)
    Para estados com menos dígitos o usuário digita normalmente.
    """
    _ignorar = [False]

    def _formatar(d: str) -> str:
        d = d[:9]
        if len(d) > 8:
            return d[:2] + "." + d[2:5] + "." + d[5:8] + "-" + d[8:]
        if len(d) > 5:
            return d[:2] + "." + d[2:5] + "." + d[5:]
        if len(d) > 2:
            return d[:2] + "." + d[2:]
        return d

    def on_change(*_):
        if _ignorar[0]:
            return
        raw = entry.get()
        digits = "".join(c for c in raw if c.isdigit())
        formatted = _formatar(digits)
        if formatted != raw:
            _ignorar[0] = True
            entry.delete(0, "end")
            entry.insert(0, formatted)
            entry.icursor(len(formatted))
            _ignorar[0] = False

    entry.bind("<KeyRelease>", on_change)


def aplicar_mascara_documento(entry) -> None:
    """
    Detecta automaticamente CPF (11 dígitos) ou RG (≤9 dígitos)
    e aplica a máscara correta conforme o usuário digita.
    """
    _ignorar = [False]

    def _formatar(d: str) -> str:
        if len(d) <= 9:
            # RG
            if len(d) > 8:
                return d[:2] + "." + d[2:5] + "." + d[5:8] + "-" + d[8:]
            if len(d) > 5:
                return d[:2] + "." + d[2:5] + "." + d[5:]
            if len(d) > 2:
                return d[:2] + "." + d[2:]
            return d
        else:
            # CPF
            d = d[:11]
            if len(d) > 9:
                return d[:3] + "." + d[3:6] + "." + d[6:9] + "-" + d[9:]
            if len(d) > 6:
                return d[:3] + "." + d[3:6] + "." + d[6:]
            if len(d) > 3:
                return d[:3] + "." + d[3:]
            return d

    def on_change(*_):
        if _ignorar[0]:
            return
        raw = entry.get()
        digits = "".join(c for c in raw if c.isdigit())
        formatted = _formatar(digits)
        if formatted != raw:
            _ignorar[0] = True
            entry.delete(0, "end")
            entry.insert(0, formatted)
            entry.icursor(len(formatted))
            _ignorar[0] = False

    entry.bind("<KeyRelease>", on_change)


def resource_path(relative: str) -> str:
    """Retorna o caminho correto tanto em desenvolvimento quanto no .exe."""
    if getattr(sys, "frozen", False):
        # Rodando como .exe — arquivos extraídos em _MEIPASS
        base = sys._MEIPASS
    else:
        # Rodando como script Python normal
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


def logo_padrao_b64() -> str:
    """Retorna o AP.png (ícone do app) já em base64, usado como logo padrão
    do formulário impresso quando nenhum logo foi configurado."""
    try:
        import base64
        with open(resource_path(os.path.join("assets", "AP.png")), "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return ""

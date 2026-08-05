import sqlite3, os, hashlib, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "achados_perdidos.db")


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nome    TEXT NOT NULL UNIQUE,
            senha   TEXT NOT NULL,
            nivel   TEXT NOT NULL CHECK(nivel IN ('Administrador', 'Operador'))
        );

        CREATE TABLE IF NOT EXISTS objetos (
            id                   TEXT PRIMARY KEY,
            nome                 TEXT NOT NULL,
            descricao            TEXT,
            data_encontrada      TEXT,
            local_encontrado     TEXT,
            quem_encontrou       TEXT,
            empresa              TEXT,
            id_usuario_cadastro  INTEGER,
            status               TEXT DEFAULT 'disponivel'
                                 CHECK(status IN ('disponivel', 'retirado', 'arquivado')),
            FOREIGN KEY (id_usuario_cadastro) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS retiradas (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            id_objeto            TEXT NOT NULL,
            nome_retirante       TEXT,
            documento            TEXT,
            empresa              TEXT,
            data_retirada        TEXT,
            id_usuario_retirada  INTEGER,
            FOREIGN KEY (id_objeto)           REFERENCES objetos(id),
            FOREIGN KEY (id_usuario_retirada) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS log_atividades (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT NOT NULL,
            usuario   TEXT NOT NULL,
            acao      TEXT NOT NULL,
            id_objeto TEXT,
            detalhe   TEXT
        );

        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        );
    """)

    # Migração: remove foto_path se existir
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(objetos)").fetchall()]
        if "foto_path" in cols:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS objetos_new (
                    id                   TEXT PRIMARY KEY,
                    nome                 TEXT NOT NULL,
                    descricao            TEXT,
                    data_encontrada      TEXT,
                    local_encontrado     TEXT,
                    quem_encontrou       TEXT,
                    empresa              TEXT,
                    id_usuario_cadastro  INTEGER,
                    status               TEXT DEFAULT 'disponivel'
                                         CHECK(status IN ('disponivel', 'retirado', 'arquivado')),
                    FOREIGN KEY (id_usuario_cadastro) REFERENCES usuarios(id)
                );
                INSERT INTO objetos_new
                    SELECT id, nome, descricao, data_encontrada, local_encontrado,
                           quem_encontrou, empresa, id_usuario_cadastro,
                           CASE WHEN status NOT IN ('disponivel','retirado','arquivado')
                                THEN 'disponivel' ELSE status END
                    FROM objetos;
                DROP TABLE objetos;
                ALTER TABLE objetos_new RENAME TO objetos;
            """)
    except Exception:
        pass

    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios (nome, senha, nivel) VALUES (?, ?, ?)",
                  ("admin", _hash("admin"), "Administrador"))

    conn.commit()
    conn.close()
    arquivar_objetos_antigos()


# ── Arquivamento automático ───────────────────────────────────────────────────

def arquivar_objetos_antigos():
    limite = datetime.date.today() - datetime.timedelta(days=90)
    conn   = get_conn()
    rows   = conn.execute(
        "SELECT id, data_encontrada FROM objetos WHERE status = 'disponivel'"
    ).fetchall()
    para_arquivar = []
    for row in rows:
        raw  = (row["data_encontrada"] or "").strip()
        data = None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                data = datetime.datetime.strptime(raw, fmt).date()
                break
            except ValueError:
                continue
        if not raw:
            # Data vazia — arquiva se o ID for de ano anterior
            ano_obj = int(row["id"].split("/")[1]) if "/" in row["id"] else 9999
            if ano_obj < datetime.date.today().year:
                para_arquivar.append(row["id"])
        elif data and data <= limite:
            para_arquivar.append(row["id"])
    if para_arquivar:
        conn.executemany("UPDATE objetos SET status = 'arquivado' WHERE id = ?",
                         [(i,) for i in para_arquivar])
        conn.commit()
    conn.close()


# ── Usuários ──────────────────────────────────────────────────────────────────

def autenticar_usuario(nome: str, senha: str):
    conn = get_conn()
    row  = conn.execute("SELECT * FROM usuarios WHERE nome = ? AND senha = ?",
                        (nome.strip(), _hash(senha.strip()))).fetchone()
    conn.close()
    return dict(row) if row else None

def listar_usuarios():
    conn = get_conn()
    rows = conn.execute("SELECT id, nome, nivel FROM usuarios ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def inserir_usuario(nome: str, senha: str, nivel: str):
    conn = get_conn()
    conn.execute("INSERT INTO usuarios (nome, senha, nivel) VALUES (?, ?, ?)",
                 (nome, _hash(senha), nivel))
    conn.commit(); conn.close()

def alterar_senha(id_usuario: int, nova_senha: str):
    conn = get_conn()
    conn.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (_hash(nova_senha), id_usuario))
    conn.commit(); conn.close()

def deletar_usuario(id_usuario: int):
    conn = get_conn()
    conn.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
    conn.commit(); conn.close()


# ── Objetos ───────────────────────────────────────────────────────────────────

def proximo_id_objeto() -> str:
    ano  = datetime.date.today().year
    conn = get_conn()
    row  = conn.execute(
        "SELECT MAX(CAST(SUBSTR(id, 1, INSTR(id,'/')-1) AS INTEGER)) "
        "FROM objetos WHERE id LIKE ?",
        (f"%/{ano}",)
    ).fetchone()
    conn.close()
    ultimo = row[0] if row and row[0] is not None else 0
    return f"{ultimo + 1:03d}/{ano}"

def inserir_objeto(dados: dict):
    conn = get_conn()
    conn.execute("""INSERT INTO objetos
       (id, nome, descricao, data_encontrada, local_encontrado,
        quem_encontrou, empresa, id_usuario_cadastro, status)
       VALUES (:id, :nome, :descricao, :data_encontrada, :local_encontrado,
               :quem_encontrou, :empresa, :id_usuario_cadastro, 'disponivel')""", dados)
    conn.commit(); conn.close()
    registrar_log(dados.get("_usuario","sistema"), "Cadastrou objeto",
                  dados["id"], dados.get("nome",""))

def listar_objetos():
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM objetos
        ORDER BY
            CAST(SUBSTR(id, INSTR(id,'/')+1) AS INTEGER) DESC,
            CAST(SUBSTR(id, 1, INSTR(id,'/')-1) AS INTEGER) DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def buscar_objeto(id_objeto: str):
    conn = get_conn()
    row  = conn.execute("SELECT * FROM objetos WHERE id = ?", (id_objeto,)).fetchone()
    conn.close()
    return dict(row) if row else None

def atualizar_objeto(id_obj: str, dados: dict):
    conn = get_conn()
    conn.execute("""UPDATE objetos SET
        nome=:nome, descricao=:descricao, data_encontrada=:data_encontrada,
        local_encontrado=:local_encontrado, quem_encontrou=:quem_encontrou,
        empresa=:empresa WHERE id=:id""", {**dados, "id": id_obj})
    conn.commit(); conn.close()
    registrar_log(dados.get("_usuario","sistema"), "Editou objeto",
                  id_obj, dados.get("nome",""))

def excluir_objeto(id_obj: str, usuario: str = "sistema"):
    conn = get_conn()
    row = conn.execute("SELECT nome FROM objetos WHERE id=?", (id_obj,)).fetchone()
    nome = row["nome"] if row else ""
    conn.execute("DELETE FROM retiradas WHERE id_objeto = ?", (id_obj,))
    conn.execute("DELETE FROM objetos WHERE id = ?", (id_obj,))
    conn.commit(); conn.close()
    registrar_log(usuario, "Excluiu objeto", id_obj, nome)

def desfazer_retirada(id_obj: str, usuario: str = "sistema"):
    conn = get_conn()
    conn.execute("DELETE FROM retiradas WHERE id = (SELECT MAX(id) FROM retiradas WHERE id_objeto = ?)", (id_obj,))
    conn.execute("UPDATE objetos SET status = 'disponivel' WHERE id = ?", (id_obj,))
    conn.commit(); conn.close()
    registrar_log(usuario, "Desfez retirada", id_obj)


# ── Retiradas ─────────────────────────────────────────────────────────────────

def registrar_retirada(dados: dict):
    conn = get_conn()
    conn.execute("""INSERT INTO retiradas
       (id_objeto, nome_retirante, documento, empresa, data_retirada, id_usuario_retirada)
       VALUES (:id_objeto, :nome_retirante, :documento, :empresa,
               :data_retirada, :id_usuario_retirada)""", dados)
    conn.execute("UPDATE objetos SET status = 'retirado' WHERE id = ?", (dados["id_objeto"],))
    conn.commit(); conn.close()
    registrar_log(dados.get("_usuario", "sistema"), "Registrou retirada",
                  dados["id_objeto"], dados.get("nome_retirante", ""))

def listar_retiradas():
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*, o.nome AS nome_objeto FROM retiradas r
        JOIN objetos o ON r.id_objeto = o.id
        ORDER BY
            CAST(SUBSTR(r.id_objeto, INSTR(r.id_objeto,'/')+1) AS INTEGER) DESC,
            CAST(SUBSTR(r.id_objeto, 1, INSTR(r.id_objeto,'/')-1) AS INTEGER) DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def buscar_retirada_por_objeto(id_objeto: str):
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM retiradas WHERE id_objeto = ? ORDER BY id DESC LIMIT 1",
        (id_objeto,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def atualizar_retirada(id_retirada: int, dados: dict):
    conn = get_conn()
    conn.execute("""
        UPDATE retiradas SET
            nome_retirante = :nome_retirante,
            documento      = :documento,
            empresa        = :empresa,
            data_retirada  = :data_retirada
        WHERE id = :id
    """, {**dados, "id": id_retirada})
    conn.commit()
    conn.close()

# ── Log de atividades ─────────────────────────────────────────────────────────

def registrar_log(usuario: str, acao: str, id_objeto: str = None, detalhe: str = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO log_atividades (data_hora, usuario, acao, id_objeto, detalhe) VALUES (?,?,?,?,?)",
        (datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), usuario, acao, id_objeto, detalhe)
    )
    conn.commit(); conn.close()

def listar_log(limite: int = 200):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM log_atividades ORDER BY id DESC LIMIT ?", (limite,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mover_banco_para_appdata():
    import shutil, platform
    if platform.system() != "Windows":
        return
    appdata = os.environ.get("LOCALAPPDATA", "")
    if not appdata:
        return
    pasta   = os.path.join(appdata, "AchadosPerdidos")
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, "achados_perdidos.db")
    global DB_PATH
    if os.path.exists(destino):
        DB_PATH = destino; return
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, destino)
    DB_PATH = destino


# ── Configuração (nome da empresa / logo do formulário) ───────────────────────

def obter_config(chave: str, padrao: str = "") -> str:
    conn = get_conn()
    row = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
    conn.close()
    if row and row["valor"] is not None:
        return row["valor"]
    return padrao


def salvar_config(chave: str, valor: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO config (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, valor)
    )
    conn.commit()
    conn.close()

from contextlib import closing
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from pathlib import Path

from dotenv import load_dotenv
from werkzeug.security import check_password_hash

load_dotenv()

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

BANCO = BASE / "marketplace.db"
ARQUIVO_SQL = BASE / "database.sql"

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("PRODUCAO") == "1"
)

USUARIO = os.environ["LOGIN_USUARIO"]
SENHA_HASH = os.environ["LOGIN_SENHA_HASH"]

CAMPOS_EDITAVEIS = {"nome", "olx", "enjoei", "facebook", "shopee"}

def criar_tabela():
    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.executescript(ARQUIVO_SQL.read_text(encoding="utf-8"))

criar_tabela()

@app.before_request
def exigir_login():
    if request.endpoint in ["login", "static"]:
        return
    if "usuario" not in session:
        if request.is_json:
            return {"erro": "Sua sessão expirou. Entre de novo"}, 401
        return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def login():
    if "usuario" in session:
        return redirect(url_for("home"))
    erro = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "").strip()

        if usuario == USUARIO and check_password_hash(SENHA_HASH, senha):
            session["usuario"] = usuario
            return redirect(url_for("home"))
        erro = "Usuário ou senha inválidos"
    return render_template("login.html", erro=erro)

@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("login"))

@app.route("/home")
def home():
    return render_template("index.html")

FILTROS = {
    "todos": None,
    "vendido": 1,
    "venda": 0,
    "nao_vendido": 0
}

CONSULTA = """
SELECT id, nome, enjoei, olx, facebook, shopee, vendido
FROM produtos
WHERE nome LIKE :busca
  AND (:vendido IS NULL OR vendido = :vendido)
ORDER BY nome COLLATE NOCASE
"""


@app.route("/ofertas", methods=["GET", "POST"])
def ofertas():
    if request.method == "POST":
        pass
    return render_template("ofertas.html")

@app.route("/produtos")
def seus_produtos():
    filtro = request.args.get("filtro", "todos").lower()
    if filtro not in FILTROS:
        filtro = "todos"

    vendido = FILTROS[filtro]

    busca = request.args.get("busca", "").strip() 
    padrao = "%" + busca + "%"

    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.row_factory = sqlite3.Row

        produtos = conexao.execute(
            CONSULTA,
            {
                "busca": padrao,
                "vendido": vendido
            }
        ).fetchall()

    return render_template(
        "produtos.html",
        produtos=produtos,
        filtro=filtro,
        busca=busca,
        erro=request.args.get("erro")
    )

@app.route("/produtos/<int:produto_id>/excluir", methods=["POST"])
def excluir_produto(produto_id):
    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conexao.commit()
    return redirect(url_for("seus_produtos", busca=request.form.get("busca") or None))

@app.route("/produtos/adicionar", methods=["POST"])
def adicionar_produto():
    nome = request.form.get("nome", "").strip()
    olx = request.form.get("olx", "").strip()
    enjoei = request.form.get("enjoei", "").strip()
    facebook = request.form.get("facebook", "").strip()
    shopee = request.form.get("shopee", "").strip()

    if not nome:
        return redirect(url_for("seus_produtos", erro="Digite um produto!"))
    try:
        olx = float(olx) if olx else None
        enjoei = float(enjoei) if enjoei else None
        facebook = float(facebook) if facebook else None
        shopee = float(shopee) if shopee else None
    except ValueError:
        return redirect(url_for("seus_produtos",erro="Precos precisam ser todos numeros!"))
    
    try:
        with closing(sqlite3.connect(BANCO)) as conexao:
            conexao.execute("INSERT INTO produtos (nome, enjoei, olx, facebook, shopee) VALUES (?, ?, ?, ?, ?)",
                (nome, enjoei, olx, facebook, shopee))
            conexao.commit()
        
    except sqlite3.IntegrityError:
        return redirect(url_for("seus_produtos", erro="Este produto ja existe"))
    
    return redirect(url_for("seus_produtos"))

@app.route("/produtos/<int:produto_id>/campo", methods=["POST"])
def atualizar_campo(produto_id):
    dados = request.get_json()
    campo = dados.get("campo")
    if campo not in CAMPOS_EDITAVEIS:
        return {"erro": "Campo invalido"}, 400
    
    valor = str(dados.get("valor", "")).strip()
    try:
        valor = float(valor) if valor else None
    except ValueError:
        return {"erro": "numero invalido!"}, 400

    try:
        with closing(sqlite3.connect(BANCO)) as conexao:
            conexao.execute(f"UPDATE produtos SET {campo} = ? WHERE id = ?", (valor, produto_id))
            conexao.commit()

    except sqlite3.IntegrityError:
        return {"erro": "valor nao permitido"}, 400
    
    return{"ok": True}

@app.route("/produtos/<int:produto_id>/alternar_vendido", methods=["POST"])
def alternar_vendido(produto_id):
    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.execute("UPDATE produtos SET vendido = 1 - vendido WHERE id = ?", (produto_id,))
        conexao.commit()
    return redirect(url_for("seus_produtos", 
                            busca=request.form.get("busca") or None,
                            filtro=request.form.get("filtro") or None))

if __name__ == "__main__":
    app.run(debug=True)



from contextlib import closing
from flask import Flask, render_template, request, redirect, url_for
import math
import sqlite3
from pathlib import Path

BANCO = Path(__file__).with_name("marketplace.db")
ARQUIVO_SQL = Path(__file__).with_name("database.sql")

app = Flask(__name__)

CAMPOS_EDITAVEIS = {"nome", "olx", "enjoei", "facebook", "shopee"}

def criar_tabela():
    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.executescript(ARQUIVO_SQL.read_text(encoding="utf-8"))

criar_tabela()

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

@app.route("/")
def home():
    return render_template("index.html")


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
        busca=busca
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

if __name__ == "__main__":
    app.run(debug=True)



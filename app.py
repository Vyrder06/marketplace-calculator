from contextlib import closing
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
    # Migração: adicionar colunas se não existirem
    with closing(sqlite3.connect(BANCO)) as conexao:
        cursor = conexao.cursor()
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = [row[1] for row in cursor.fetchall()]
        if 'loja_vendida' not in colunas:
            cursor.execute("ALTER TABLE produtos ADD COLUMN loja_vendida TEXT CHECK (loja_vendida IN ('olx', 'enjoei', 'facebook', 'shopee'))")
        if 'preco_venda' not in colunas:
            cursor.execute("ALTER TABLE produtos ADD COLUMN preco_venda REAL CHECK (preco_venda > 0)")
        if 'modo_enjoei' not in colunas:
            cursor.execute("ALTER TABLE produtos ADD COLUMN modo_enjoei TEXT CHECK (modo_enjoei IN ('classico', 'turbinado'))")
        if 'valor_liquido' not in colunas:
            cursor.execute("ALTER TABLE produtos ADD COLUMN valor_liquido REAL")
        conexao.commit()

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
SELECT id, nome, enjoei, olx, facebook, shopee, vendido, loja_vendida, preco_venda, modo_enjoei, valor_liquido
FROM produtos
WHERE nome LIKE :busca
  AND (:vendido IS NULL OR vendido = :vendido)
ORDER BY nome COLLATE NOCASE
"""


def calcular_valor_liquido(loja, preco, modo_enjoei=None):
    preco = float(preco)

    if loja == 'olx':
        # OLX - sem taxas
        return {
            'valor_liquido': round(preco, 2),
            'taxa_total': 0,
            'detalhes': 'Sem taxas no OLX'
        }

    elif loja == 'facebook':
        # Facebook - sem taxas
        return {
            'valor_liquido': round(preco, 2),
            'taxa_total': 0,
            'detalhes': 'Sem taxas no Facebook Marketplace'
        }

    elif loja == 'enjoei':
        # Enjoei - % + tarifa fixa por faixa + taxa de saque R$3
        if modo_enjoei == 'turbinado':
            percentual = 0.18
        else:
            percentual = 0.12  # classico

        # Tarifa fixa por faixa de preço
        if preco <= 15:
            tarifa_fixa = 2.50
        elif preco <= 50:
            tarifa_fixa = 5.50
        elif preco <= 70:
            tarifa_fixa = 7.50
        elif preco <= 100:
            tarifa_fixa = 8.50
        elif preco <= 150:
            tarifa_fixa = 13.50
        elif preco <= 300:
            tarifa_fixa = 22.50
        else:  # até 500
            tarifa_fixa = 25.00

        taxa_percentual = preco * percentual
        taxa_saque = 3.00
        taxa_total = taxa_percentual + tarifa_fixa + taxa_saque
        valor_liquido = preco - taxa_total

        return {
            'valor_liquido': round(valor_liquido, 2),
            'taxa_total': round(taxa_total, 2),
            'detalhes': f'Enjoei {modo_enjoei.capitalize()}: {percentual*100:.0f}% (R${taxa_percentual:.2f}) + Tarifa R${tarifa_fixa:.2f} + Saque R${taxa_saque:.2f} = R${taxa_total:.2f}'
        }

    elif loja == 'shopee':
        if preco <= 79.99:
            percentual = 0.20
            taxa_fixa = 4.00
        elif preco <= 99.99:
            percentual = 0.14
            taxa_fixa = 16.00
        elif preco <= 199.99:
            percentual = 0.14
            taxa_fixa = 20.00
        elif preco <= 499.99:
            percentual = 0.14
            taxa_fixa = 26.00
        else:  # 500+
            percentual = 0.14
            taxa_fixa = 26.00

        taxa_cpf = 3.00
        taxa_percentual = preco * percentual
        taxa_total = taxa_percentual + taxa_fixa + taxa_cpf
        valor_liquido = preco - taxa_total

        return {
            'valor_liquido': round(valor_liquido, 2),
            'taxa_total': round(taxa_total, 2),
            'detalhes': f'Shopee: {percentual*100:.0f}% (R${taxa_percentual:.2f}) + Taxa fixa R${taxa_fixa:.2f} + CPF R${taxa_cpf:.2f} = R${taxa_total:.2f}'
        }

    return {
        'valor_liquido': round(preco, 2),
        'taxa_total': 0,
        'detalhes': 'Loja não reconhecida'
    }


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
            conexao.execute("""
                INSERT INTO produtos (nome, enjoei, olx, facebook, shopee)
                VALUES (?, ?, ?, ?, ?)
            """, (nome, enjoei, olx, facebook, shopee))
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
    busca = request.form.get("busca") or None
    filtro = request.form.get("filtro", "todos").lower()
    if filtro not in FILTROS:
        filtro = "todos"

    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.row_factory = sqlite3.Row
        produto = conexao.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()

    if not produto:
        return redirect(url_for("seus_produtos", busca=busca, filtro=filtro))

    # Ao marcar como vendido, pedir loja e preço antes de alterar o status.
    if produto['vendido'] == 0:
        with closing(sqlite3.connect(BANCO)) as conexao:
            conexao.row_factory = sqlite3.Row
            produtos = conexao.execute(
                CONSULTA,
                {
                    "busca": f"%{busca or ''}%",
                    "vendido": FILTROS[filtro],
                }
            ).fetchall()

        return render_template(
            "produtos.html",
            produtos=produtos,
            filtro=filtro,
            busca=busca or "",
            erro=None,
            modal_venda={
                "produto_id": produto_id,
                "produto_nome": produto["nome"],
                "precos": {
                    loja: produto[loja]
                    for loja in ("olx", "enjoei", "facebook", "shopee")
                },
                "busca": busca or "",
                "filtro": filtro,
            },
        )
    else:
        # Se está marcando como NÃO VENDIDO (vendido = 1 -> 0), limpa info de venda
        with closing(sqlite3.connect(BANCO)) as conexao:
            conexao.execute("""
                UPDATE produtos
                SET vendido = 0, loja_vendida = NULL, preco_venda = NULL, modo_enjoei = NULL, valor_liquido = NULL
                WHERE id = ?
            """, (produto_id,))
            conexao.commit()

    return redirect(url_for("seus_produtos", busca=busca, filtro=filtro))


@app.route("/produtos/<int:produto_id>/confirmar_venda", methods=["POST"])
def confirmar_venda(produto_id):
    busca = request.form.get("busca") or None
    filtro = request.form.get("filtro") or None

    loja_vendida = request.form.get("loja_vendida")
    preco_venda = request.form.get("preco_venda")
    modo_enjoei = request.form.get("modo_enjoei")  # apenas para Enjoei

    lojas_validas = {"olx", "enjoei", "facebook", "shopee"}
    if loja_vendida not in lojas_validas or not preco_venda:
        return redirect(url_for("seus_produtos", busca=busca, filtro=filtro, erro="Selecione a loja e o preço de venda"))

    try:
        preco_venda = float(preco_venda)
    except ValueError:
        return redirect(url_for("seus_produtos", busca=busca, filtro=filtro, erro="Preço inválido"))
    if preco_venda <= 0:
        return redirect(url_for("seus_produtos", busca=busca, filtro=filtro, erro="O preço deve ser maior que zero"))
    if loja_vendida == "enjoei" and request.form.get("modo_enjoei") not in {"classico", "turbinado"}:
        return redirect(url_for("seus_produtos", busca=busca, filtro=filtro, erro="Selecione o modo do Enjoei"))
    if loja_vendida != "enjoei":
        modo_enjoei = None

    # Calcular valor líquido
    resultado = calcular_valor_liquido(loja_vendida, preco_venda, modo_enjoei)

    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.execute("""
            UPDATE produtos
            SET vendido = 1,
                loja_vendida = ?,
                preco_venda = ?,
                modo_enjoei = ?,
                valor_liquido = ?,
                {campo_loja} = ?
            WHERE id = ?
        """.format(campo_loja=loja_vendida), (
            loja_vendida,
            preco_venda,
            modo_enjoei,
            resultado['valor_liquido'],
            resultado['valor_liquido'],
            produto_id,
        ))
        conexao.commit()

    return redirect(url_for("seus_produtos", busca=busca, filtro=filtro))


if __name__ == "__main__":
    app.run(debug=True)

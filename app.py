from contextlib import closing

from flask import Flask, render_template, request
import math
import sqlite3
from pathlib import Path

BANCO = Path(__file__).with_name("marketplace.db")
ARQUIVO_SQL = Path(__file__).with_name("database.sql")

app = Flask(__name__)


tabela_taxas = {
    "olx": {
        "taxa_percentual": 0.00,
        "taxa_fixa": 0.00
    },
    "facebook": {
        "taxa_percentual": 0.00,
        "taxa_fixa": 0.00
    },
    "enjoei": {
        "modos": {
            "turbinado": {
                "taxa_percentual": 0.18
            },
            "classico": {
                "taxa_percentual": 0.12
            } 
        },
        "faixas": [
            {"min": 0, "max": 15, "fixa": 2.50},
            {"min": 15, "max": 50, "fixa": 5.50},
            {"min": 50, "max": 70, "fixa": 7.50},
            {"min": 70, "max": 100, "fixa": 8.50},
            {"min": 100, "max": 150, "fixa": 13.50},
            {"min": 150, "max": 300, "fixa": 22.50},
            {"min": 300, "max": 500, "fixa": 25.00},
            {"min": 500, "max": float("inf"), "fixa": 40.00}
        ],
        "taxa_saque": 3.00
    },
    "shopee": {
        "faixas": [
            {"min": 0, "max": 80, "percentual": 0.20, "fixa": 4.00},
            {"min": 80, "max": 100, "percentual": 0.14, "fixa": 16.00},
            {"min": 100, "max": 200, "percentual": 0.14, "fixa": 20.00},
            {"min": 200, "max": 500, "percentual": 0.14, "fixa": 26.00},
            {"min": 500, "max": float("inf"), "percentual": 0.14, "fixa": 26.00}
        ],
        "taxa_cpf": 3.00
    }
}
def calcular_taxas(marketplace, preco, modo="classico"):
    marketplace = marketplace.strip().lower()

    if marketplace in ("olx", "facebook"):
        return 0.0
    if marketplace == "enjoei":
        regras = tabela_taxas["enjoei"]

        for faixa in regras["faixas"]:
            if faixa["min"] < preco <= faixa["max"]:
                percentual = regras["modos"][modo]["taxa_percentual"]
                return preco * percentual + faixa["fixa"]
    
    elif marketplace == "shopee":
        regras = tabela_taxas["shopee"]

        for faixa in regras["faixas"]:
            if faixa["min"] < preco <= faixa["max"]:
                return (
                    preco * faixa["percentual"]
                    + faixa["fixa"]
                    +regras["taxa_cpf"]
                )
    raise ValueError ("O Marketplace e o preço devem ser valores usáveis.")
    


def vender_por(marketplace, preco, modo="classico"):
    marketplace = marketplace.strip().lower()


    if marketplace in ("olx", "facebook"):
        return preco 
    if marketplace == "enjoei":
        regras = tabela_taxas["enjoei"]
        percentual = regras["modos"][modo]["taxa_percentual"]
        for faixa in regras["faixas"]:
            taxa_fixa = faixa["fixa"]

            valor_vender = (preco + taxa_fixa) / (1 - percentual)
            if faixa["min"] < valor_vender <= faixa["max"]:
                return math.ceil(valor_vender * 100) / 100
    elif marketplace == "shopee": 
        regras = tabela_taxas["shopee"]
        for faixa in regras["faixas"]:
            taxa_fixa = faixa["fixa"]
            percentual = faixa["percentual"]

            valor_vender = (preco + taxa_fixa + regras["taxa_cpf"]) / (1 - percentual)
            if faixa["min"] < valor_vender <= faixa["max"]:
                return math.ceil(valor_vender * 100) / 100

    raise ValueError ("Marketplace e/ou preço inválido!")

def criar_tabela():
    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.executescript(ARQUIVO_SQL.read_text(encoding="utf-8"))

criar_tabela()

FILTROS = {"todos": None, "vendido": 1, "nao_vendido": 0}

CONSULTA = """
SELECT id, nome, enjoei, olx, facebook, shopee, vendido
FROM produtos
WHERE nome LIKE :busca
  AND (:vendido IS NULL OR vendido = :vendido)
ORDER BY nome
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
    filtro = request.args.get("filtro", "todos")
    vendido = FILTROS.get(filtro)
    busca = "%" + request.args.get("busca", "") + "%"
    with closing(sqlite3.connect(BANCO)) as conexao:
        conexao.row_factory = sqlite3.Row
        produtos = conexao.execute(CONSULTA, {"busca": busca, "vendido": vendido}).fetchall()
    return render_template("produtos.html", produtos=produtos, filtro=filtro)

if __name__ == "__main__":
    app.run(debug=True)



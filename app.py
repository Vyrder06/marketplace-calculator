from flask import Flask, render_template, request

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
    raise ValueError("Marketplace ou faixa de preço inválida.")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        custo = float(request.form["custo"])
        marketplace = request.form["marketplace"]
        preco = float(request.form["preco"])

        lucro = preco - custo
        taxa = calcular_taxas(marketplace, preco, modo=request.form.get("modo-enjoei", "classico"))
        receber = preco - taxa
        return render_template(
        "cadastro.html",
        lucro=lucro,
        nome=nome,
        taxa=taxa,
        receber=receber
        )

    return render_template("cadastro.html")

@app.route("/ofertas", methods=["GET", "POST"])
def ofertas():
    if request.method == "POST":
        pass
    return render_template("ofertas.html")

if __name__ == "__main__":
    app.run(debug=True)

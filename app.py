from flask import Flask, render_template, request

app = Flask(__name__)


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

        return render_template(
        "cadastro.html",
        lucro=lucro,
        nome=nome
        )

    return render_template("cadastro.html")


if __name__ == "__main__":
    app.run(debug=True)

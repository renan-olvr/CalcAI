import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
from datetime import datetime
import math

app = Flask(__name__)


# ---------------------------
# CRIA O BANCO E A TABELA
# ---------------------------

def init_db():

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT(100) NOT NULL UNIQUE,
                password TEXT NOT NULL,
                registration_date TEXT,
                update_date TEXT
                );
    """)

    # Save (commit) the changes
    con.commit()

    # Close the connection
    con.close()

# ---------------------------
# INICIA O BANCO ANTES DE QQ COISA NA APLICAÇÃO
# ---------------------------
init_db()

# ---------------------------
# ENTRAR COMO CONVIDADO
# ---------------------------
@app.route("/guest")
def guest():
    return render_template("index.html")
      

# ---------------------------
# TELA DE LOGIN
# ---------------------------

@app.route("/")
def login_page():
    return render_template("login.html")



# ---------------------------
# LOGIN /
# ---------------------------

# função ok, apenas precisa exibir a mensagem na prórpia página de registro,
# ao invés de redirecionar para outra página, caso o os dados estejam incorretos.
@app.route("/login", methods=["POST"])
def login():

    email = request.form["username"]
    password = request.form["password"]

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
                SELECT *
                FROM users
                WHERE (email = ? AND password = ?)
                """,
                (email, password) )

    user_exists = cur.fetchone()

    con.close()

    # Verifica se o usuário existe e redireciona para a página de boas-vindas, caso contrário, exibe uma mensagem de erro
    if user_exists:
        return render_template("index.html")
        # substituir pela página desejada no projeto

    else:
        return render_template("login.html", erro="Usuário ou senha incorretos")


# ---------------------------
# REGISTRARAR USUÁRIO
# ---------------------------

@app.route("/register")
def register_page():
    return render_template("register.html")



@app.route("/register_user", methods=["POST"])
def register_user():

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        return render_template("register.html", erro="As senhas digitas não coincidem")


    try:
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        cur.execute("""
                    INSERT INTO users(username, email, password, registration_date, update_date)
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (username, email, password, datetime.now(), datetime.now()) )

        # Save (commit) the changes
        con.commit()

        # Close the connection
        #con.close()

        return redirect(url_for("login_page"))

     # Usuário ou e-mail duplicado (UNIQUE)
    except sqlite3.IntegrityError:
        return render_template("register.html", erro="Usuário ou e-mail já cadastrado.")

     # Qualquer outro erro inesperado
    except Exception as e:

        print(f"Erro inesperado: {e}")

        return render_template("register.html", erro="Ocorreu um erro inesperado.")

    finally:
        try:
            con.close()
        except:
            pass


# ---------------------------
# INTEGRAÇÃO
# ---------------------------
# ================= TAXAS (BrasilAPI) =================
BRASIL_API_TAXAS = "https://brasilapi.com.br/api/taxas/v1"

TAXAS_FALLBACK = {
    "SELIC": 13.75,
    "CDI": 13.65,
    "IPCA": 4.52,
}

def get_taxas_mercado():
    try:
        resp = requests.get(BRASIL_API_TAXAS, timeout=8)
        resp.raise_for_status()

        dados = resp.json()

        mapa = {
            item["nome"].upper(): item["valor"]
            for item in dados
        }

        return {
            "selic": mapa.get("SELIC", TAXAS_FALLBACK["SELIC"]),
            "cdi": mapa.get("CDI", TAXAS_FALLBACK["CDI"]),
            "ipca": mapa.get("IPCA", TAXAS_FALLBACK["IPCA"]),
            "fonte": "BrasilAPI"
        }

    except Exception as e:
        return {
            **TAXAS_FALLBACK,
            "fonte": f"fallback ({str(e)[:40]})"
        }

# ================= PRODUTOS =================
TAXAS_PRODUTO = {
    "CDB": {
        "fator_min": 0.95,
        "fator_max": 1.10,
        "indexer": "CDI",
        "label": "% do CDI"
    },

    "LCI": {
        "fator_min": 0.85,
        "fator_max": 0.95,
        "indexer": "CDI",
        "label": "% do CDI (isento IR)"
    },

    "LCA": {
        "fator_min": 0.87,
        "fator_max": 0.97,
        "indexer": "CDI",
        "label": "% do CDI (isento IR)"
    },

    "SELIC": {
        "fator_min": 1.00,
        "fator_max": 1.00,
        "indexer": "SELIC",
        "label": "100% da SELIC"
    },
}

def calcular_projecao(aporte_mensal, taxa_aa_decimal, meses):

    taxa_mm = math.pow(1 + taxa_aa_decimal, 1 / 12) - 1

    patrimonio = 0.0
    total_aportado = 0.0

    historico = []

    for _ in range(meses):

        patrimonio = patrimonio * (1 + taxa_mm) + aporte_mensal
        total_aportado += aporte_mensal

        historico.append({
            "patrimonio": round(patrimonio, 2),
            "aportado": round(total_aportado, 2),
            "rendimento": round(patrimonio - total_aportado, 2),
        })

    return historico

# ================= API TAXAS =================
@app.route("/api/taxas", methods=["GET"])
def taxas():
    return jsonify(get_taxas_mercado())

# ================= API INVESTIMENTOS =================
@app.route("/api/investimentos", methods=["POST"])
def investimentos():

    data = request.json or {}

    try:
        renda = float(data.get("renda", 0))
        percentual = float(data.get("percentual", 0))
        aporte_adicional = float(data.get("aporte_adicional", 0))
        tipo = str(data.get("tipo", "CDB")).upper()
        meses = int(data.get("periodo", 12))

    except (ValueError, TypeError) as e:
        return jsonify({
            "erro": f"Parâmetros inválidos: {e}"
        }), 400

    if meses < 1 or meses > 600:
        return jsonify({
            "erro": "Período deve ser entre 1 e 600 meses."
        }), 400

    taxas = get_taxas_mercado()

    produto = TAXAS_PRODUTO.get(
        tipo,
        TAXAS_PRODUTO["CDB"]
    )

    taxa_base = (
        taxas["selic"]
        if produto["indexer"] == "SELIC"
        else taxas["cdi"]
    )

    fator_medio = (
        produto["fator_min"] +
        produto["fator_max"]
    ) / 2

    taxa_aa = (
        taxa_base / 100
    ) * fator_medio

    aporte_mensal = (
        renda * (percentual / 100)
    ) + aporte_adicional

    historico = calcular_projecao(
        aporte_mensal,
        taxa_aa,
        meses
    )

    ultimo = historico[-1]

    rendimento = ultimo["rendimento"]

    pct_rendimento = (
        (rendimento / ultimo["aportado"]) * 100
        if ultimo["aportado"] > 0
        else 0
    )

    resultado = {
        "tipo": tipo,
        "periodo_meses": meses,
        "aporte_mensal": round(aporte_mensal, 2),
        "patrimonio_final": ultimo["patrimonio"],
        "total_aportado": ultimo["aportado"],
        "rendimento_total": round(rendimento, 2),
        "pct_rendimento": round(pct_rendimento, 2),
        "taxa_efetiva_aa": round(taxa_aa * 100, 4),
        "taxa_indexador": produto["label"],
        "taxas_referencia": taxas,
        "historico": historico,
    }

    return jsonify(resultado)


# ---------------------------
# EXECUÇÃO
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)
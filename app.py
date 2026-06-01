import sqlite3
from flask import Flask, render_template, request, redirect, url_for

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
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
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
    return render_template("welcome.html", username="Visitante")
      

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

    username = request.form["username"]
    password = request.form["password"]

    con = sqlite3.connect("database.db")
    cur = con.cursor()

    cur.execute("""
                SELECT * FROM users
                WHERE username = ? AND password = ?
                """,
                (username, password) )

    user_exists = cur.fetchone()

    con.close()

    # Verifica se o usuário existe e redireciona para a página de boas-vindas, caso contrário, exibe uma mensagem de erro
    if user_exists:
        return render_template("welcome.html", username=username)
        # substituir pela página desejada no projeto

    else:
        return render_template("login.html", erro="Usuário ou senha incorretos")


# ---------------------------
# REGISTRARAR USUÁRIO
# ---------------------------

@app.route("/register")
def register_page():
    return render_template("register.html")



# função ok, apenas precisa exibir a mensagem na prórpia página de registro,
# ao invés de redirecionar para outra página, caso o usuário já exista.
@app.route("/register_user", methods=["POST"])
def register_user():

    username = request.form["username"]
    password = request.form["password"]

    try:
        con = sqlite3.connect("database.db")
        cur = con.cursor()

        cur.execute("""
                    INSERT INTO users(username, password)
                    VALUES(?, ?)
                    """,
                    (username, password) )

        # Save (commit) the changes
        con.commit()

        # Close the connection
        con.close()

        return redirect(url_for("login_page"))

    except:
        return "Usuário já cadastrado. Por favor, escolha outro nome de usuário."


# ---------------------------
# EXECUÇÃO
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)
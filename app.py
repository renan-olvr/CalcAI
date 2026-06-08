import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

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
        return render_template("calculator.html")
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
# EXECUÇÃO
# ---------------------------

if __name__ == "__main__":
    app.run(debug=True)
import os
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import re
from cs50 import SQL
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///ordenes.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        dia = request.form.get("dia")
        ordenes = db.execute("SELECT * FROM list_ord WHERE dia = :dia", dia=dia)

        # print (ordenes[0]["id_Operador"])
        return render_template("index.html", mordenes=ordenes, dia=dia)
    else:
        dia = datetime.date.today()

        ordenes = db.execute("SELECT * FROM list_ord WHERE dia = :dia", dia=dia)

        # print (ordenes[0]["id_Operador"])
        return render_template("index.html", mordenes=ordenes,dia=dia)


@app.route("/busca_operadores")
def busca_operadores():
    """Busca Operadores"""

    # retrieve q from HTML form
    q = request.args.get("q") + "%"
    # Finds any postal code, city and state that start with q
    operadores = db.execute("SELECT * FROM operadores WHERE nombre LIKE :q", q=q)
    return jsonify(operadores)

@app.route("/carga", methods=["GET", "POST"])
@login_required
def carga():
    if request.method == "POST":
        # empezamos a instanciar todo lo que trae el POST para insertar en DB

        tipo_Op = request.form.get("tipo_Op")
        cantidad = request.form.get("cantidad")
        tipo_Activo = request.form.get("tipo_Activo")
        producto = request.form.get("producto")
        mes = request.form.get("mes")
        precio = request.form.get("precio")
        al_Mercado = request.form.get("al_Mercado")
        id_Cliente = request.form.get("id_Cliente")
        A_C = ""
        if request.form.get("AC_abre") == "A":
            A_C = "A"

        if request.form.get("AC_cancela") == "C":
            A_C = "C"

        prima = request.form.get("prima")
        id_Operador = request.form.get("id_Operador")
        id_Metodo = request.form.get("id_Metodo")
        id_Cliente = request.form.get("id_Cliente")
        dia = datetime.date.today()
        hora = request.form.get("hora")
        id_user = session["user_id"]
        print (A_C)
        db.execute("INSERT INTO list_ord (tipo_Op, cantidad, tipo_Activo, producto, mes, precio, al_Mercado, id_Cliente, A_C, prima, id_Operador, id_Metodo, dia, hora, id_User) Values(:tipo_Op, :cantidad, :tipo_Activo, :producto, :mes, :precio, :al_Mercado, :id_Cliente, :A_C, :prima, :id_Operador, :id_Metodo, :dia, :hora, :id_user)",
                    tipo_Op=tipo_Op, cantidad=cantidad, tipo_Activo=tipo_Activo, producto=producto, mes=mes, precio=precio, al_Mercado=al_Mercado, id_Cliente=id_Cliente, A_C=A_C, prima=prima, id_Operador=id_Operador, id_Metodo=id_Metodo, dia=dia, hora=hora, id_user=id_user)

        return redirect("/")

    else:
        return render_template("carga.html")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide stock", 400)
        if not request.form.get("shares"):
            return apology("must provide quantity", 400)

        try:
            cantidad = int(request.form.get("shares"))
        except:
            return apology("shares must be a positive integer", 400)

        if cantidad < 1:
            return apology("can´t buy zero or a negative number of shares", 400)

        quote = lookup(request.form.get("symbol"))
        if quote == None:
            return apology("stock not found", 400)

        cash_remaining = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
        in_cash_remaining = cash_remaining[0]["cash"]

        if quote["price"] * int(request.form.get("shares")) > in_cash_remaining:
            return apology("not enough funds", 400)

        else:  # ejecutar insert
            userid = session["user_id"]
            fecha = datetime.datetime.now()
            stock = quote["symbol"]
            tipo = "BUY"
            precio = quote["price"]
            volumen = quote["price"] * int(request.form.get("shares"))

            db.execute("INSERT INTO anotes (username, fecha, stock, tipo, cantidad, precio) Values(:username, :fecha, :stock, :tipo, :cantidad, :precio)",
                       username=userid, fecha=fecha, stock=stock, tipo=tipo, cantidad=cantidad, precio=precio)

            db.execute("UPDATE users SET cash = cash - :volumen where id = :userid", volumen=volumen, userid=userid)

            cash_remaining = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
            in_cash_remaining = cash_remaining[0]["cash"]

            return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    acciones_db = db.execute(
        "SELECT fecha, stock, tipo, cantidad, precio FROM anotes WHERE username = :userid", userid=session["user_id"])

    cash_remaining = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
    in_cash_remaining = cash_remaining[0]["cash"]

    for i in acciones_db:
        quote = lookup(i["stock"])
        i["name"] = quote["name"]

    return render_template("history.html", acciones=acciones_db)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide stock", 400)

        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("stock not found", 400)

        return render_template("quoted.html", name=quote["name"], price=quote["price"], symbol=quote["symbol"])

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Nombre de Usuario requerido", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Contraseña requerida", 400)

        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("La contraseña y su confirmación deben ser idénticas", 400)

        existe = db.execute("SELECT * FROM users WHERE username = :username",
                            username=request.form.get("username"))

        if len(existe) == 1:
            return apology("Usuario existente", 400)
        # INSERT new username, and login (vía Session ID)

        session["user_id"] = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash_p)",
                                        username=request.form.get("username"), hash_p=generate_password_hash(request.form.get("password")))

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide stock", 400)
        if not request.form.get("shares"):
            return apology("must provide quantity", 400)

        try:
            cantidad = int(request.form.get("shares"))
        except:
            return apology("shares must be a positive integer", 400)

        if cantidad < 1:
            return apology("can´t buy zero or a negative number of shares", 400)

        quote = lookup(request.form.get("symbol"))
        if quote == None:
            return apology("stock not found", 400)

        acciones_db = db.execute("SELECT username, stock, SUM(cantidad) AS cant_total FROM anotes WHERE username = :userid and stock = :stock GROUP BY stock",
                                 userid=session["user_id"], stock=request.form.get("symbol"))
        if len(acciones_db) == 0:
            return apology("stock not found", 400)

        if acciones_db[0]["cant_total"] < int(request.form.get("shares")):
            return apology("not enough shares to sell", 400)

        else:  # ejecutar insert
            userid = session["user_id"]
            fecha = datetime.datetime.now()
            stock = quote["symbol"]
            tipo = "SELL"
            cantidad = int(request.form.get("shares"))
            precio = quote["price"]
            volumen = quote["price"] * cantidad

            db.execute("INSERT INTO anotes (username, fecha, stock, tipo, cantidad, precio) Values(:username, :fecha, :stock, :tipo, :cantidad, :precio)",
                       username=userid, fecha=fecha, stock=stock, tipo=tipo, cantidad=cantidad * -1, precio=precio)

            db.execute("UPDATE users SET cash = cash + :volumen where id = :userid", volumen=volumen, userid=userid)

            cash_remaining = db.execute("SELECT cash FROM users WHERE id = :userid", userid=session["user_id"])
            in_cash_remaining = cash_remaining[0]["cash"]
            return redirect("/")

    else:

        acciones_db = db.execute(
            "SELECT stock, SUM(cantidad) AS cant_total FROM anotes WHERE username = :userid GROUP BY stock HAVING cant_total > 0", userid=session["user_id"])
        return render_template("sell.html", acciones=acciones_db)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
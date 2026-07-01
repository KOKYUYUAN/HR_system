from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "LEON_KOKYY2002"
DB = "database.db"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            carsem_id     TEXT UNIQUE NOT NULL,
            full_name     TEXT NOT NULL,
            department    TEXT NOT NULL,
            position      TEXT NOT NULL,
            phone         TEXT,
            email         TEXT,
            date_joined   TEXT NOT NULL,
            registered_by TEXT NOT NULL,
            created_at    TEXT NOT NULL
        )
    """)

    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("admin", "admin123", "hr_admin"))
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("viewer", "viewer123", "hr_viewer"))
    except sqlite3.IntegrityError:
        pass

    conn.commit()
    conn.close()


def generate_carsem_id():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM employees")
    count = c.fetchone()[0]
    conn.close()
    return f"CARSEM-{count + 1:04d}"



def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    employees = conn.execute(
        "SELECT * FROM employees ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("dashboard.html", employees=employees,
                           username=session["username"], role=session["role"])


@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" not in session:
        return redirect(url_for("login"))

    if session["role"] != "hr_admin":
        flash("Access denied. Only HR Admin can register employees.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        carsem_id   = generate_carsem_id()
        full_name   = request.form["full_name"]
        department  = request.form["department"]
        position    = request.form["position"]
        phone       = request.form["phone"]
        email       = request.form["email"]
        date_joined = request.form["date_joined"]
        created_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute("""
            INSERT INTO employees
            (carsem_id, full_name, department, position, phone, email,
             date_joined, registered_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (carsem_id, full_name, department, position, phone, email,
              date_joined, session["username"], created_at))
        conn.commit()
        conn.close()

        flash(f"Employee registered! CARSEM ID: {carsem_id}", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html", next_id=generate_carsem_id(),
                           username=session["username"], role=session["role"])



@app.route("/users")
def users():
    if "username" not in session:
        return redirect(url_for("login"))
    if session["role"] != "hr_admin":
        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    conn = get_db()
    all_users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return render_template("users.html", users=all_users,
                           username=session["username"], role=session["role"])


@app.route("/users/add", methods=["POST"])
def add_user():
    if "username" not in session or session["role"] != "hr_admin":
        return redirect(url_for("login"))

    username = request.form["username"].strip()
    password = request.form["password"]
    role     = request.form["role"]

    try:
        conn = get_db()
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                     (username, password, role))
        conn.commit()
        conn.close()
        flash(f"User '{username}' added successfully!", "success")
    except sqlite3.IntegrityError:
        flash(f"Username '{username}' already exists.", "error")

    return redirect(url_for("users"))


@app.route("/users/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "username" not in session or session["role"] != "hr_admin":
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted.", "success")
    return redirect(url_for("users"))



if __name__ == "__main__":
    init_db()
    print("Default accounts:")
    print("  Admin  -> username: admin   | password: admin123")
    print("  Viewer -> username: viewer  | password: viewer123")
    print("Open http://127.0.0.1:5000")
    app.run(debug=True)

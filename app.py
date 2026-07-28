from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "smart-maintenance-secret-key"

DATABASE = "maintenance.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            skill TEXT,
            phone TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workorders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment TEXT,
            problem TEXT NOT NULL,
            technician TEXT,
            priority TEXT,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)

    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))

    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, ("admin", "1234", "Admin"))

    conn.commit()
    conn.close()


create_database()


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND password = ?
        """, (username, password)).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    equipment_count = conn.execute(
        "SELECT COUNT(*) FROM equipment"
    ).fetchone()[0]

    technician_count = conn.execute(
        "SELECT COUNT(*) FROM technicians"
    ).fetchone()[0]

    workorder_count = conn.execute(
        "SELECT COUNT(*) FROM workorders"
    ).fetchone()[0]

    pending_count = conn.execute("""
        SELECT COUNT(*) FROM workorders
        WHERE status = 'Pending'
    """).fetchone()[0]

    progress_count = conn.execute("""
        SELECT COUNT(*) FROM workorders
        WHERE status = 'In Progress'
    """).fetchone()[0]

    completed_count = conn.execute("""
        SELECT COUNT(*) FROM workorders
        WHERE status = 'Completed'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        equipment_count=equipment_count,
        technician_count=technician_count,
        workorder_count=workorder_count,
        pending_count=pending_count,
        progress_count=progress_count,
        completed_count=completed_count
    )


@app.route("/equipment", methods=["GET", "POST"])
def equipment():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name", "")
        location = request.form.get("location", "")

        if name:
            conn.execute("""
                INSERT INTO equipment (name, location)
                VALUES (?, ?)
            """, (name, location))

            conn.commit()

    equipment_list = conn.execute("""
        SELECT * FROM equipment
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "equipment.html",
        equipment=equipment_list
    )


@app.route("/equipment/delete/<int:id>")
def delete_equipment(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    conn.execute(
        "DELETE FROM equipment WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/equipment")


@app.route("/technicians", methods=["GET", "POST"])
def technicians():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":

        name = request.form.get("name", "")
        skill = request.form.get("skill", "")
        phone = request.form.get("phone", "")

        if name:
            conn.execute("""
                INSERT INTO technicians (name, skill, phone)
                VALUES (?, ?, ?)
            """, (name, skill, phone))

            conn.commit()

    technician_list = conn.execute("""
        SELECT * FROM technicians
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "technicians.html",
        technicians=technician_list
    )


@app.route("/technicians/delete/<int:id>")
def delete_technician(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    conn.execute(
        "DELETE FROM technicians WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/technicians")


@app.route("/workorders", methods=["GET", "POST"])
def workorders():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method == "POST":

        equipment = request.form.get("equipment", "")
        problem = request.form.get("problem", "")
        technician = request.form.get("technician", "")
        priority = request.form.get("priority", "Medium")

        if problem:
            conn.execute("""
                INSERT INTO workorders
                (equipment, problem, technician, priority, status)
                VALUES (?, ?, ?, ?, 'Pending')
            """, (
                equipment,
                problem,
                technician,
                priority
            ))

            conn.commit()

    workorder_list = conn.execute("""
        SELECT * FROM workorders
        ORDER BY id DESC
    """).fetchall()

    equipment_list = conn.execute("""
        SELECT * FROM equipment
        ORDER BY name
    """).fetchall()

    technician_list = conn.execute("""
        SELECT * FROM technicians
        ORDER BY name
    """).fetchall()

    conn.close()

    return render_template(
        "workorders.html",
        workorders=workorder_list,
        equipment=equipment_list,
        technicians=technician_list
    )


@app.route("/workorders/status/<int:id>/<status>")
def update_status(id, status):

    if "user_id" not in session:
        return redirect("/login")

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Completed"
    ]

    if status not in allowed_statuses:
        return redirect("/workorders")

    conn = get_db()

    conn.execute("""
        UPDATE workorders
        SET status = ?
        WHERE id = ?
    """, (status, id))

    conn.commit()
    conn.close()

    return redirect("/workorders")


@app.route("/workorders/delete/<int:id>")
def delete_workorder(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    conn.execute(
        "DELETE FROM workorders WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/workorders")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
      )

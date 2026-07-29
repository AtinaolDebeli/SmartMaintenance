from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
from datetime import datetime

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


    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)


    # EQUIPMENT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        location TEXT,
        photo TEXT,
        qr_code TEXT,
        status TEXT DEFAULT 'Active'
    )
    """)


    # TECHNICIANS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS technicians(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        skill TEXT,
        phone TEXT
    )
    """)


    # WORK ORDERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workorders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment TEXT,
        problem TEXT,
        technician TEXT,
        priority TEXT,
        status TEXT DEFAULT 'Pending',
        date TEXT
    )
    """)


    # INVENTORY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        quantity INTEGER,
        minimum INTEGER
    )
    """)


    # SUPPLIERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        item TEXT
    )
    """)


    # PREVENTIVE MAINTENANCE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preventive(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment TEXT,
        schedule TEXT,
        next_date TEXT
    )
    """)


    # DEFAULT ADMIN
    user = cursor.execute(
        "SELECT * FROM users WHERE username='admin'"
    ).fetchone()


    if user is None:

        cursor.execute("""
        INSERT INTO users
        (username,password,role)
        VALUES(?,?,?)
        """,
        (
            "admin",
            "1234",
            "Admin"
        ))


    conn.commit()
    conn.close()



create_database()
# LOGIN

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()

        user = conn.execute("""
        SELECT * FROM users
        WHERE username=? AND password=?
        """,
        (username,password)).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect("/")

        return render_template(
            "login.html",
            error="Invalid login"
        )

    return render_template("login.html")



# DASHBOARD

@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")


    conn = get_db()

    equipment = conn.execute(
        "SELECT COUNT(*) FROM equipment"
    ).fetchone()[0]


    technicians = conn.execute(
        "SELECT COUNT(*) FROM technicians"
    ).fetchone()[0]


    jobs = conn.execute(
        "SELECT COUNT(*) FROM workorders"
    ).fetchone()[0]


    stock = conn.execute(
        "SELECT COUNT(*) FROM inventory"
    ).fetchone()[0]


    conn.close()


    return render_template(
        "dashboard.html",
        username=session["username"],
        equipment=equipment,
        technicians=technicians,
        jobs=jobs,
        stock=stock
    )



# EQUIPMENT

@app.route("/equipment", methods=["GET","POST"])
def equipment_page():

    if "user_id" not in session:
        return redirect("/login")


    conn=get_db()


    if request.method=="POST":

        name=request.form.get("name")
        category=request.form.get("category")
        location=request.form.get("location")

        conn.execute("""
        INSERT INTO equipment
        (name,category,location)
        VALUES(?,?,?)
        """,
        (
            name,
            category,
            location
        ))

        conn.commit()


    data=conn.execute("""
    SELECT * FROM equipment
    ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "equipment.html",
        equipment=data
    )



# TECHNICIANS

@app.route("/technicians", methods=["GET","POST"])
def technician_page():

    if "user_id" not in session:
        return redirect("/login")


    conn=get_db()


    if request.method=="POST":

        name=request.form.get("name")
        skill=request.form.get("skill")
        phone=request.form.get("phone")


        conn.execute("""
        INSERT INTO technicians
        (name,skill,phone)
        VALUES(?,?,?)
        """,
        (
            name,
            skill,
            phone
        ))


        conn.commit()



    data=conn.execute("""
    SELECT * FROM technicians
    ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "technicians.html",
        technicians=data
    )



# WORK ORDERS

@app.route("/workorders", methods=["GET","POST"])
def workorders_page():

    if "user_id" not in session:
        return redirect("/login")


    conn=get_db()


    if request.method=="POST":

        equipment=request.form.get("equipment")
        problem=request.form.get("problem")
        technician=request.form.get("technician")
        priority=request.form.get("priority")


        conn.execute("""
        INSERT INTO workorders
        (equipment,problem,technician,priority,date)
        VALUES(?,?,?,?,?)
        """,
        (
            equipment,
            problem,
            technician,
            priority,
            datetime.now()
        ))


        conn.commit()



    jobs=conn.execute("""
    SELECT * FROM workorders
    ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "workorders.html",
        workorders=jobs
    )# INVENTORY / STORE

@app.route("/inventory", methods=["GET","POST"])
def inventory():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    if request.method=="POST":

        item = request.form.get("item")
        quantity = request.form.get("quantity")
        minimum = request.form.get("minimum")


        conn.execute("""
        INSERT INTO inventory
        (item,quantity,minimum)
        VALUES(?,?,?)
        """,
        (
            item,
            quantity,
            minimum
        ))

        conn.commit()


    items = conn.execute("""
    SELECT * FROM inventory
    ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "inventory.html",
        items=items
    )



# SUPPLIERS

@app.route("/suppliers", methods=["GET","POST"])
def suppliers():

    if "user_id" not in session:
        return redirect("/login")


    conn=get_db()


    if request.method=="POST":

        name=request.form.get("name")
        phone=request.form.get("phone")
        item=request.form.get("item")


        conn.execute("""
        INSERT INTO suppliers
        (name,phone,item)
        VALUES(?,?,?)
        """,
        (
            name,
            phone,
            item
        ))

        conn.commit()


    data=conn.execute("""
    SELECT * FROM suppliers
    ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "suppliers.html",
        suppliers=data
    )



# PREVENTIVE MAINTENANCE

@app.route("/preventive", methods=["GET","POST"])
def preventive():

    if "user_id" not in session:
        return redirect("/login")


    conn=get_db()


    if request.method=="POST":

        equipment=request.form.get("equipment")
        schedule=request.form.get("schedule")
        next_date=request.form.get("next_date")


        conn.execute("""
        INSERT INTO preventive
        (equipment,schedule,next_date)
        VALUES(?,?,?)
        """,
        (
            equipment,
            schedule,
            next_date
        ))

        conn.commit()


    data=conn.execute("""
    SELECT * FROM preventive
    ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "preventive.html",
        preventive=data
    )



# LOGOUT

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")



# START PROGRAM

if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
        )
    

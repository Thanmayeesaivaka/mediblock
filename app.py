from flask import Flask, render_template, request, redirect, session
from database import add_user, find_user, load_blocks
from blockchain import create_block, verify_chain

app = Flask(__name__)
app.secret_key = "mediblock_secret"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("login.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = {
            "username": request.form["username"],
            "password": request.form["password"],
            "fullname": request.form["fullname"],
            "age": request.form["age"],
            "gender": request.form["gender"],
            "phone": request.form["phone"],
            "address": request.form["address"],
            "role": request.form["role"]
        }
        add_user(user)
        return redirect("/")
    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"].strip()
    password = request.form["password"].strip()
    role = request.form["role"].strip()

    user = find_user(username, password, role)

    if user:
        session["user"] = username
        session["role"] = role

        if role == "Doctor":
            return redirect("/doctor")
        elif role == "Patient":
            return redirect("/patient")
        elif role == "Admin":
            return redirect("/admin")
        else:
            return redirect("/insurance")

    return render_template("login.html", error="Invalid Login Credentials")


# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    return render_template("admin.html", user=session.get("user"))


# ---------------- DOCTOR ----------------
@app.route("/doctor", methods=["GET","POST"])
def doctor():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        patient = request.form["patient"]
        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]

        create_block(patient, session["user"], diagnosis, prescription)

    blocks = load_blocks()
    return render_template("doctor.html", blocks=blocks)


# ---------------- PATIENT ----------------
@app.route("/patient")
def patient():

    if "user" not in session:
        return redirect("/")

    blocks = load_blocks()
    valid = verify_chain()

    return render_template("patient.html", blocks=blocks, valid=valid)


# ---------------- INSURANCE ----------------
@app.route("/insurance")
def insurance():

    if "user" not in session:
        return redirect("/")

    blocks = load_blocks()
    valid = verify_chain()

    return render_template("insurance.html", blocks=blocks, valid=valid)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


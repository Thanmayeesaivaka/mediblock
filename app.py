from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
import hashlib
import base64
import os

from database import add_user, find_user

app = Flask(__name__)
app.secret_key = "mediblock_secret"

# =====================================
# MongoDB CONNECTION
# =====================================

MONGO_URI = "mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["mediblock"]

patients = db["patients"]
treatments = db["treatments"]
reports = db["reports"]
shared = db["shared"]
claims = db["claims"]
findings = db["findings"]

# =====================================
# ENCRYPTION
# =====================================

key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
cipher = Fernet(key)

# =====================================
# HOME
# =====================================

@app.route("/")
def home():
    return render_template("login.html")

# =====================================
# REGISTER
# =====================================

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
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
        except Exception as e:
            return str(e)

    return render_template("register.html")

# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["POST"])
def login():
    try:
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        user = find_user(username, password, role)

        if user:
            session["user"] = username
            session["role"] = role

            role = role.lower()

            if role == "doctor":
                return redirect("/doctor")
            elif role == "patient":
                return redirect("/patient")
            elif role == "research":
                return redirect("/research")
            elif role == "insurance":
                return redirect("/insurance")
            elif role == "admin":
                return redirect("/admin")

        return render_template("login.html", error="Invalid Credentials")

    except Exception as e:
        return str(e)

# =====================================
# DOCTOR MODULE
# =====================================

@app.route("/doctor")
def doctor():
    if "user" not in session:
        return redirect("/")
    return render_template("doctor.html")

# View patient records
@app.route("/view_records")
def view_records():
    data = list(treatments.find())
    return render_template("view_records.html", data=data)

# Update treatment
@app.route("/update_treatment", methods=["GET","POST"])
def update_treatment():
    if request.method == "POST":
        patient = request.form["patient"]
        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]

        text = f"Diagnosis:{diagnosis}|Prescription:{prescription}"
        enc = cipher.encrypt(text.encode())

        treatments.insert_one({
            "patient": patient,
            "doctor": session["user"],
            "data": base64.b64encode(enc).decode(),
            "date": datetime.now()
        })

        return "Updated Successfully"

    return render_template("update_treatment.html")

# Upload report
@app.route("/upload_report", methods=["GET","POST"])
def upload_report():
    if request.method == "POST":
        patient = request.form["patient"]
        report_name = request.form["report"]

        reports.insert_one({
            "patient": patient,
            "report": report_name,
            "doctor": session["user"]
        })

        return "Uploaded"

    return render_template("upload_report.html")

# Share data
@app.route("/share_data", methods=["GET","POST"])
def share_data():
    if request.method == "POST":
        patient = request.form["patient"]
        to = request.form["to"]

        shared.insert_one({
            "patient": patient,
            "shared_to": to
        })

        return "Shared"

    return render_template("share_data.html")

# =====================================
# PATIENT MODULE
# =====================================

@app.route("/patient")
def patient():
    return render_template("patient.html")

# View history
@app.route("/history")
def history():
    data = list(treatments.find({"patient": session["user"]}))
    return render_template("history.html", data=data)

# Grant access
@app.route("/grant_access", methods=["GET","POST"])
def grant_access():
    if request.method == "POST":
        doctor = request.form["doctor"]

        shared.insert_one({
            "patient": session["user"],
            "doctor": doctor
        })

        return "Access Granted"

    return render_template("grant_access.html")

# =====================================
# RESEARCH MODULE
# =====================================

@app.route("/research")
def research():
    return render_template("research.html")

@app.route("/analyze")
def analyze():
    data = list(reports.find())
    return render_template("analyze.html", data=data)

@app.route("/submit_findings", methods=["GET","POST"])
def submit_findings():
    if request.method == "POST":
        f = request.form["finding"]

        findings.insert_one({
            "finding": f,
            "user": session["user"]
        })

        return "Submitted"

    return render_template("submit_findings.html")

# =====================================
# INSURANCE MODULE
# =====================================

@app.route("/insurance")
def insurance():
    return render_template("insurance.html")

@app.route("/claims", methods=["GET","POST"])
def claims_func():
    if request.method == "POST":
        claims.insert_one({
            "patient": request.form["patient"],
            "amount": request.form["amount"]
        })
        return "Claim Added"

    return render_template("claims.html")

@app.route("/approve", methods=["POST"])
def approve():
    claim = request.form["claim"]
    claims.update_one({"_id": claim}, {"$set": {"status": "approved"}})
    return "Approved"

# =====================================
# ADMIN MODULE
# =====================================

@app.route("/admin")
def admin():
    return render_template("admin.html")

# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =====================================
# RUN
# =====================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
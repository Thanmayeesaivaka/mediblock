from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
from bson import ObjectId
import base64
import os

from database import add_user, find_user

app = Flask(__name__)
app.secret_key = "mediblock_secret"

# =====================================
# MongoDB CONNECTION (SAFE)
# =====================================

MONGO_URI = "mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["mediblock"]

patients = db["patients"]
treatments = db["treatments"]
reports = db["reports"]
shared = db["shared"]
claims = db["claims"]
findings = db["findings"]

# Test connection
try:
    client.server_info()
    print("MongoDB Connected")
except:
    print("MongoDB Connection Failed")


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
            return f"Error: {e}"

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
            elif role in ["research", "research analyst"]:
                return redirect("/research")
            elif role in ["insurance", "insurance company"]:
                return redirect("/insurance")
            elif role == "admin":
                return redirect("/admin")

        return render_template("login.html", error="Invalid Credentials")

    except Exception as e:
        return f"Login Error: {e}"


# =====================================
# DOCTOR MODULE
# =====================================

@app.route("/doctor")
def doctor():
    if "user" not in session:
        return redirect("/")
    return render_template("doctor.html")


@app.route("/view_records")
def view_records():
    if "user" not in session:
        return redirect("/")
    data = list(treatments.find().limit(20))
    return render_template("view_records.html", data=data)


@app.route("/update_treatment", methods=["GET","POST"])
def update_treatment():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            text = f"Diagnosis:{request.form['diagnosis']}|Prescription:{request.form['prescription']}"
            enc = cipher.encrypt(text.encode())

            treatments.insert_one({
                "patient": request.form["patient"],
                "doctor": session["user"],
                "data": base64.b64encode(enc).decode(),
                "date": datetime.now()
            })

            return render_template("update_treatment.html", message="Updated Successfully")

        except Exception as e:
            return f"Error: {e}"

    return render_template("update_treatment.html")


@app.route("/upload_report", methods=["GET","POST"])
def upload_report():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        reports.insert_one({
            "patient": request.form["patient"],
            "report": request.form["report"],
            "doctor": session["user"]
        })
        return render_template("upload_report.html", message="Uploaded")

    return render_template("upload_report.html")


@app.route("/share_data", methods=["GET","POST"])
def share_data():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        shared.insert_one({
            "patient": request.form["patient"],
            "shared_to": request.form["to"]
        })
        return render_template("share_data.html", message="Shared")

    return render_template("share_data.html")


# =====================================
# PATIENT MODULE
# =====================================

@app.route("/patient")
def patient():
    if "user" not in session:
        return redirect("/")
    return render_template("patient.html")


@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")
    data = list(treatments.find({"patient": session["user"]}).limit(20))
    return render_template("history.html", data=data)


@app.route("/grant_access", methods=["GET","POST"])
def grant_access():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        shared.insert_one({
            "patient": session["user"],
            "doctor": request.form["doctor"]
        })
        return render_template("grant_access.html", message="Access Granted")

    return render_template("grant_access.html")


# =====================================
# RESEARCH MODULE
# =====================================

@app.route("/research")
def research():
    if "user" not in session:
        return redirect("/")
    return render_template("research.html")


@app.route("/analyze")
def analyze():
    if "user" not in session:
        return redirect("/")
    data = list(reports.find().limit(20))
    return render_template("analyze.html", data=data)


@app.route("/submit_findings", methods=["GET","POST"])
def submit_findings():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        findings.insert_one({
            "finding": request.form["finding"],
            "user": session["user"]
        })
        return render_template("submit_findings.html", message="Submitted")

    return render_template("submit_findings.html")


# =====================================
# INSURANCE MODULE
# =====================================

@app.route("/insurance")
def insurance():
    if "user" not in session:
        return redirect("/")
    return render_template("insurance.html")


@app.route("/claims", methods=["GET","POST"])
def claims_func():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        claims.insert_one({
            "patient": request.form["patient"],
            "amount": request.form["amount"],
            "status": "Pending"
        })
        return render_template("claims.html", message="Claim Added")

    data = list(claims.find().limit(20))
    return render_template("claims.html", data=data)


@app.route("/approve", methods=["POST"])
def approve():

    if "user" not in session:
        return redirect("/")

    try:
        claim_id = request.form["claim"]
        claims.update_one(
            {"_id": ObjectId(claim_id)},
            {"$set": {"status": "Approved"}}
        )
        return "Approved"
    except:
        return "Error updating claim"


# =====================================
# ADMIN MODULE
# =====================================

@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/")
    return render_template("admin.html")


# =====================================
# LOGOUT
# =====================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =====================================
# RUN (LOCAL ONLY)
# =====================================

if __name__ == "__main__":
    app.run(debug=True)
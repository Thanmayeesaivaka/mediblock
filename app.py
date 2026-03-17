from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
import hashlib
import base64

from database import add_user, find_user
from blockchain import verify_chain

app = Flask(__name__)
app.secret_key = "mediblock_secret"


# =====================================
# MongoDB CONNECTION
# =====================================

client = MongoClient("mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority")
db = client["mediblock"]

patients_collection = db["patients"]
reports_collection = db["reports"]
treatments_collection = db["treatments"]
shared_collection = db["shared_data"]
appointments_collection = db["appointments"]

research_findings_collection = db["research_findings"]
claims_collection = db["claims"]


# =====================================
# ENCRYPTION
# =====================================

encryption_key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
cipher = Fernet(encryption_key)


# =====================================
# HOME
# =====================================

@app.route("/")
def home():
    return render_template("main_home.html")


# =====================================
# REGISTER
# =====================================

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
        return redirect("/login")

    return render_template("register.html")


# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        user = find_user(username, password, role)

        if user:

            session["user"] = username
            session["role"] = role.lower()

            if session["role"] == "doctor":
                return redirect("/doctor")

            elif session["role"] == "patient":
                return redirect("/patient")

            elif session["role"] in ["research analyst","research"]:
                return redirect("/research")

            elif session["role"] in ["insurance company","insurance"]:
                return redirect("/insurance")

            elif session["role"] == "admin":
                return redirect("/admin")

        return render_template("login.html", error="Invalid Login Credentials")

    return render_template("login.html")


# =====================================
# DOCTOR MODULE
# =====================================

@app.route("/doctor")
def doctor():
    if "user" not in session:
        return redirect("/")
    return render_template("doctor.html")


@app.route("/update_treatment", methods=["GET","POST"])
def update_treatment():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        patient_id = request.form["patient"]
        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]

        text = f"Diagnosis: {diagnosis} | Prescription: {prescription}"

        encrypted = cipher.encrypt(text.encode())

        treatments_collection.insert_one({
            "patient_id": patient_id,
            "doctor": session["user"],
            "encrypted_treatment": base64.b64encode(encrypted).decode(),
            "hash_key": hashlib.sha256(text.encode()).hexdigest(),
            "date": datetime.now().strftime("%Y-%m-%d")
        })

        return render_template("update_treatment.html", message="Treatment Stored Successfully")

    return render_template("update_treatment.html")


# =====================================
# PATIENT MODULE
# =====================================

@app.route("/patient")
def patient():
    if "user" not in session:
        return redirect("/")
    return render_template("patient.html")


# =====================================
# RESEARCH MODULE
# =====================================

@app.route("/research")
def research():
    if "user" not in session:
        return redirect("/")
    return render_template("research.html")


@app.route("/analyze_info")
def analyze_info():

    if "user" not in session:
        return redirect("/")

    reports = list(reports_collection.find())

    return render_template("analyze_info.html", data=reports)


@app.route("/generate_reports")
def generate_reports():

    if "user" not in session:
        return redirect("/")

    treatments = list(treatments_collection.find())
    disease_count = {}

    for t in treatments:

        encrypted = base64.b64decode(t["encrypted_treatment"])
        text = cipher.decrypt(encrypted).decode()

        disease = text.split("|")[0].replace("Diagnosis:", "").strip()

        disease_count[disease] = disease_count.get(disease, 0) + 1

    labels = list(disease_count.keys()) or ["No Data"]
    values = list(disease_count.values()) or [1]

    return render_template("generate_reports.html", labels=labels, values=values)


@app.route("/submit_findings", methods=["GET","POST"])
def submit_findings():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        research_findings_collection.insert_one({
            "finding": request.form["finding"],
            "details": request.form["details"],
            "submitted_by": session["user"],
            "date": datetime.now().strftime("%Y-%m-%d")
        })

        return render_template("submit_findings.html", message="Submitted Successfully")

    return render_template("submit_findings.html")


# =====================================
# INSURANCE MODULE
# =====================================

@app.route("/insurance")
def insurance():
    if "user" not in session:
        return redirect("/")
    return render_template("insurance.html")


@app.route("/verify_policy", methods=["GET","POST"])
def verify_policy():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        return render_template("verify_policy.html", message="Policy Verified")

    return render_template("verify_policy.html")


@app.route("/receive_claim", methods=["GET","POST"])
def receive_claim():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        claims_collection.insert_one({
            "claim_id": request.form["claim"],
            "patient": request.form["patient"],
            "amount": request.form["amount"],
            "status": "Pending",
            "payment": "Not Paid"
        })

    return render_template("receive_claim.html")


@app.route("/validate_claim")
def validate_claim():

    if "user" not in session:
        return redirect("/")

    claims = list(claims_collection.find())
    return render_template("validate_claim.html", claims=claims)


@app.route("/approve_claim", methods=["GET","POST"])
def approve_claim():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        claims_collection.update_one(
            {"claim_id": request.form["claim"]},
            {"$set": {"status": request.form["status"]}}
        )

    return render_template("approve_claim.html")


@app.route("/update_payment", methods=["GET","POST"])
def update_payment():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        claims_collection.update_one(
            {"claim_id": request.form["claim"]},
            {"$set": {"payment": request.form["payment"]}}
        )

    return render_template("update_payment.html")


# =====================================
# ADMIN
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
# RUN APP
# =====================================

if __name__ == "__main__":
    app.run()
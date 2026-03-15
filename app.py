from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
import hashlib
import base64

from database import add_user, find_user, load_blocks
from blockchain import create_block, verify_chain

app = Flask(__name__)
app.secret_key = "mediblock_secret"


# ---------------- MongoDB CONNECTION ----------------

client = MongoClient("mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority")

db = client["mediblock"]

patients_collection = db["patients"]
reports_collection = db["reports"]
treatments_collection = db["treatments"]
shared_collection = db["shared_data"]
appointments_collection = db["appointments"]

# Research collections
research_reports_collection = db["research_reports"]
research_findings_collection = db["research_findings"]


# ---------------- ENCRYPTION ----------------

encryption_key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
cipher = Fernet(encryption_key)


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():
    return render_template("login.html")


# =====================================================
# REGISTER
# =====================================================

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


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]
    role = request.form["role"]

    user = find_user(username, password, role)

    if user:

        session["user"] = username
        session["role"] = role

        if role == "Doctor":
            return redirect("/doctor")

        elif role == "Patient":
            return redirect("/patient")

        elif role == "Research":
            return redirect("/research")

        elif role == "Admin":
            return redirect("/admin")

    return render_template("login.html", error="Invalid Login Credentials")


# =====================================================
# DOCTOR DASHBOARD
# =====================================================

@app.route("/doctor")
def doctor():

    if "user" not in session:
        return redirect("/")

    return render_template("doctor.html")


# =====================================================
# UPDATE TREATMENT
# =====================================================

@app.route("/update_treatment", methods=["GET","POST"])
def update_treatment():

    if request.method == "POST":

        patient_id = request.form["patient"]
        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]

        treatment_text = f"Diagnosis: {diagnosis} | Prescription: {prescription}"

        treatment_bytes = treatment_text.encode()

        hash_key = hashlib.sha256(treatment_bytes).hexdigest()

        encrypted_data = cipher.encrypt(treatment_bytes)

        treatment_document = {

            "patient_id": patient_id,
            "doctor": session["user"],
            "encrypted_treatment": base64.b64encode(encrypted_data).decode(),
            "hash_key": hash_key,
            "date": datetime.now().strftime("%Y-%m-%d")

        }

        treatments_collection.insert_one(treatment_document)

        return render_template("update_treatment.html", message="Treatment Stored Successfully")

    return render_template("update_treatment.html")


# =====================================================
# RESEARCH ANALYST DASHBOARD
# =====================================================

@app.route("/research")
def research():

    if "user" not in session:
        return redirect("/")

    return render_template("research_home.html")


# =====================================================
# ANALYZE INFORMATION
# =====================================================

@app.route("/analyze_info")
def analyze_info():

    reports = list(reports_collection.find())

    data = []

    for r in reports:

        data.append({
            "patient_id": r["patient_id"],
            "report_name": r["report_name"],
            "uploaded_by": r["uploaded_by"],
            "hash": r["hash_key"]
        })

    return render_template("analyze_info.html", data=data)


# =====================================================
# GENERATE REPORTS (CHART DATA)
# =====================================================

@app.route("/generate_reports")
def generate_reports():

    treatments = list(treatments_collection.find())

    disease_count = {}

    for t in treatments:

        encrypted_data = base64.b64decode(t["encrypted_treatment"])
        decrypted_data = cipher.decrypt(encrypted_data).decode()

        disease = decrypted_data.split("|")[0].replace("Diagnosis:", "").strip()

        if disease in disease_count:
            disease_count[disease] += 1
        else:
            disease_count[disease] = 1

    labels = list(disease_count.keys())
    values = list(disease_count.values())

    return render_template("generate_reports.html", labels=labels, values=values)


# =====================================================
# SUBMIT FINDINGS
# =====================================================

@app.route("/submit_findings", methods=["GET","POST"])
def submit_findings():

    if request.method == "POST":

        finding = request.form["finding"]
        details = request.form["details"]

        research_findings_collection.insert_one({

            "finding": finding,
            "details": details,
            "submitted_by": session["user"],
            "date": datetime.now().strftime("%Y-%m-%d")

        })

        return render_template("submit_findings.html", message="Findings Submitted Successfully")

    return render_template("submit_findings.html")


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =====================================================
# RUN APP
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)
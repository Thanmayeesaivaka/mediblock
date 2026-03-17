from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
import hashlib
import base64
import os

from database import add_user, find_user, load_blocks
from blockchain import create_block, verify_chain

app = Flask(__name__)
app.secret_key = "mediblock_secret"

# =====================================
# MongoDB CONNECTION (FIXED)
# =====================================

MONGO_URI = "mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000  # prevents timeout crash
)

db = client["mediblock"]

patients_collection = db["patients"]
reports_collection = db["reports"]
treatments_collection = db["treatments"]
shared_collection = db["shared_data"]
appointments_collection = db["appointments"]

research_reports_collection = db["research_reports"]
research_findings_collection = db["research_findings"]

claims_collection = db["claims"]

# =====================================
# ENCRYPTION (SAFE)
# =====================================

encryption_key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
cipher = Fernet(encryption_key)

# =====================================
# HOME
# =====================================

@app.route("/")
def home():
    return render_template("login.html")

# =====================================
# REGISTER
# =====================================

@app.route("/register", methods=["GET", "POST"])
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
            return f"Error in Register: {str(e)}"

    return render_template("register.html")

# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
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

                elif role in ["research analyst", "research"]:
                    return redirect("/research")

                elif role in ["insurance company", "insurance"]:
                    return redirect("/insurance")

                elif role == "admin":
                    return redirect("/admin")

            return render_template("login.html", error="Invalid Login Credentials")

        except Exception as e:
            return f"Login Error: {str(e)}"

    return render_template("login.html")

# =====================================
# DOCTOR DASHBOARD
# =====================================

@app.route("/doctor")
def doctor():
    if "user" not in session:
        return redirect("/")
    return render_template("doctor.html")

# =====================================
# UPDATE TREATMENT
# =====================================

@app.route("/update_treatment", methods=["GET", "POST"])
def update_treatment():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
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

        except Exception as e:
            return f"Treatment Error: {str(e)}"

    return render_template("update_treatment.html")

# =====================================
# PATIENT DASHBOARD
# =====================================

@app.route("/patient")
def patient():
    if "user" not in session:
        return redirect("/")
    return render_template("patient.html")

# =====================================
# RESEARCH DASHBOARD
# =====================================

@app.route("/research")
def research():
    if "user" not in session:
        return redirect("/")
    return render_template("research.html")

# =====================================
# ANALYZE INFO
# =====================================

@app.route("/analyze_info")
def analyze_info():

    if "user" not in session:
        return redirect("/")

    try:
        reports = list(reports_collection.find())

        data = []
        for r in reports:
            data.append({
                "patient_id": r.get("patient_id"),
                "report_name": r.get("report_name"),
                "uploaded_by": r.get("uploaded_by"),
                "hash": r.get("hash_key")
            })

        return render_template("analyze_info.html", data=data)

    except Exception as e:
        return f"Analyze Error: {str(e)}"

# =====================================
# GENERATE REPORTS
# =====================================

@app.route("/generate_reports")
def generate_reports():

    if "user" not in session:
        return redirect("/")

    try:
        treatments = list(treatments_collection.find())
        disease_count = {}

        for t in treatments:
            encrypted_data = base64.b64decode(t["encrypted_treatment"])
            decrypted_data = cipher.decrypt(encrypted_data).decode()

            disease = decrypted_data.split("|")[0].replace("Diagnosis:", "").strip()
            disease_count[disease] = disease_count.get(disease, 0) + 1

        labels = list(disease_count.keys()) or ["No Data"]
        values = list(disease_count.values()) or [1]

        return render_template("generate_reports.html", labels=labels, values=values)

    except Exception as e:
        return f"Report Error: {str(e)}"

# =====================================
# INSURANCE DASHBOARD
# =====================================

@app.route("/insurance")
def insurance():
    if "user" not in session:
        return redirect("/")
    return render_template("insurance.html")

# =====================================
# ADMIN DASHBOARD
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
# RUN (FIXED FOR RENDER)
# =====================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
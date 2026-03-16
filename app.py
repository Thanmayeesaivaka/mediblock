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


# =================================
# MongoDB CONNECTION
# =================================

client = MongoClient("mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority")

db = client["mediblock"]

patients_collection = db["patients"]
reports_collection = db["reports"]
treatments_collection = db["treatments"]
shared_collection = db["shared_data"]
appointments_collection = db["appointments"]

research_reports_collection = db["research_reports"]
research_findings_collection = db["research_findings"]

claims_collection = db["claims"]


# =================================
# ENCRYPTION
# =================================

encryption_key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
cipher = Fernet(encryption_key)


# =================================
# HOME
# =================================

@app.route("/")
def home():
    return render_template("login.html")


# =================================
# REGISTER
# =================================

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


# =================================
# LOGIN
# =================================

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

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

            elif role in ["research analyst","research"]:
                return redirect("/research")

            elif role in ["insurance company","insurance"]:
                return redirect("/insurance")

            elif role == "admin":
                return redirect("/admin")

        return render_template("login.html", error="Invalid Login Credentials")

    return render_template("login.html")


# =================================
# DOCTOR DASHBOARD
# =================================

@app.route("/doctor")
def doctor():

    if "user" not in session:
        return redirect("/")

    return render_template("doctor.html")


# =================================
# UPDATE TREATMENT
# =================================

@app.route("/update_treatment", methods=["GET","POST"])
def update_treatment():

    if "user" not in session:
        return redirect("/")

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

        return render_template(
            "update_treatment.html",
            message="Treatment Stored Successfully"
        )

    return render_template("update_treatment.html")


# =================================
# PATIENT DASHBOARD
# =================================

@app.route("/patient")
def patient():

    if "user" not in session:
        return redirect("/")

    return render_template("patient.html")


# =================================
# RESEARCH DASHBOARD
# =================================

@app.route("/research")
def research():

    if "user" not in session:
        return redirect("/")

    return render_template("research.html")


# =================================
# ANALYZE INFORMATION
# =================================

@app.route("/analyze_info")
def analyze_info():

    if "user" not in session:
        return redirect("/")

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


# =================================
# GENERATE REPORTS
# =================================

@app.route("/generate_reports")
def generate_reports():

    if "user" not in session:
        return redirect("/")

    treatments = list(treatments_collection.find())

    disease_count = {}

    for t in treatments:

        encrypted_data = base64.b64decode(t["encrypted_treatment"])
        decrypted_data = cipher.decrypt(encrypted_data).decode()

        disease = decrypted_data.split("|")[0].replace("Diagnosis:", "").strip()

        disease_count[disease] = disease_count.get(disease, 0) + 1

    labels = list(disease_count.keys())
    values = list(disease_count.values())

    if len(labels) == 0:
        labels = ["No Data"]
        values = [1]

    return render_template(
        "generate_reports.html",
        labels=labels,
        values=values
    )


# =================================
# SUBMIT FINDINGS
# =================================

@app.route("/submit_findings", methods=["GET","POST"])
def submit_findings():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        finding = request.form["finding"]
        details = request.form["details"]

        research_findings_collection.insert_one({

            "finding": finding,
            "details": details,
            "submitted_by": session["user"],
            "date": datetime.now().strftime("%Y-%m-%d")

        })

        return render_template(
            "submit_findings.html",
            message="Findings Submitted Successfully"
        )

    return render_template("submit_findings.html")


# =================================
# INSURANCE DASHBOARD
# =================================

@app.route("/insurance")
def insurance():

    if "user" not in session:
        return redirect("/")

    return render_template("insurance.html")


# VERIFY POLICY

@app.route("/verify_policy", methods=["GET","POST"])
def verify_policy():

    if request.method == "POST":

        policy = request.form["policy"]
        patient = request.form["patient"]

    return render_template("verify_policy.html")


# RECEIVE CLAIM

@app.route("/receive_claim", methods=["GET","POST"])
def receive_claim():

    if request.method == "POST":

        claim = request.form["claim"]
        patient = request.form["patient"]
        amount = request.form["amount"]

        claims_collection.insert_one({
            "claim_id": claim,
            "patient": patient,
            "amount": amount
        })

    return render_template("receive_claim.html")


# VALIDATE CLAIM

@app.route("/validate_claim")
def validate_claim():

    claims = list(claims_collection.find())

    return render_template("validate_claim.html", claims=claims)


# APPROVE CLAIM

@app.route("/approve_claim", methods=["GET","POST"])
def approve_claim():

    if request.method == "POST":

        claim = request.form["claim"]
        status = request.form["status"]

        claims_collection.update_one(
            {"claim_id": claim},
            {"$set": {"status": status}}
        )

    return render_template("approve_claim.html")


# UPDATE PAYMENT

@app.route("/update_payment", methods=["GET","POST"])
def update_payment():

    if request.method == "POST":

        claim = request.form["claim"]
        payment = request.form["payment"]

        claims_collection.update_one(
            {"claim_id": claim},
            {"$set": {"payment": payment}}
        )

    return render_template("update_payment.html")


# =================================
# ADMIN
# =================================

@app.route("/admin")
def admin():

    if "user" not in session:
        return redirect("/")

    return render_template("admin.html")


# =================================
# LOGOUT
# =================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =================================
# RUN APP
# =================================

if __name__ == "__main__":
    app.run(debug=True)
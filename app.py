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

client = MongoClient(
"mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"
)

db = client["mediblock"]

patients_collection = db["patients"]
reports_collection = db["reports"]
treatments_collection = db["treatments"]
shared_collection = db["shared_data"]
appointments_collection = db["appointments"]


# ---------------- ENCRYPTION SETUP ----------------

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

        elif role == "Admin":
            return redirect("/admin")

        else:
            return redirect("/insurance")

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
# VIEW PATIENT RECORDS
# =====================================================

@app.route("/view_records")
def view_records():

    patients = list(patients_collection.find())

    return render_template("view_records.html", patients=patients)


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
# TREATMENT HISTORY
# =====================================================

@app.route("/treatment_history")
def treatment_history():

    treatments = list(treatments_collection.find())

    history = []

    for t in treatments:

        encrypted_data = base64.b64decode(t["encrypted_treatment"])
        decrypted_data = cipher.decrypt(encrypted_data)

        history.append({

            "patient_id": t["patient_id"],
            "doctor": t["doctor"],
            "treatment": decrypted_data.decode(),
            "hash": t["hash_key"]

        })

    return render_template("treatment_history.html", history=history)


# =====================================================
# UPLOAD REPORT
# =====================================================

@app.route("/upload_report", methods=["GET","POST"])
def upload_report():

    if request.method == "POST":

        patient_id = request.form["pid"]
        file = request.files["report"]

        file_data = file.read()

        hash_key = hashlib.sha256(file_data).hexdigest()

        encrypted_data = cipher.encrypt(file_data)

        report_document = {

            "patient_id": patient_id,
            "report_name": file.filename,
            "encrypted_report": base64.b64encode(encrypted_data).decode(),
            "hash_key": hash_key,
            "uploaded_by": session["user"]

        }

        reports_collection.insert_one(report_document)

        return render_template("upload_report.html", message="Report Uploaded Successfully")

    return render_template("upload_report.html")


# =====================================================
# SHARE DATA
# =====================================================

@app.route("/share_data", methods=["GET","POST"])
def share_data():

    if request.method == "POST":

        patient_id = request.form["patient"]
        receiver = request.form["receiver"]

        share_text = f"{patient_id}-{receiver}-{session['user']}"

        hash_key = hashlib.sha256(share_text.encode()).hexdigest()

        share_document = {

            "patient_id": patient_id,
            "shared_with": receiver,
            "shared_by": session["user"],
            "hash_key": hash_key,
            "date": datetime.now().strftime("%Y-%m-%d")

        }

        shared_collection.insert_one(share_document)

        return render_template("share_data.html", message="Data Shared Successfully", key=hash_key)

    return render_template("share_data.html")


# =====================================================
# CREATE APPOINTMENT
# =====================================================

@app.route("/create_appointment", methods=["GET","POST"])
def create_appointment():

    if request.method == "POST":

        appointment = {

            "patient_id": request.form["patient_id"],
            "patient_name": request.form["patient_name"],
            "doctor": request.form["doctor"],
            "date": request.form["date"],
            "time": request.form["time"],
            "status": "Scheduled"

        }

        appointments_collection.insert_one(appointment)

        return redirect("/doctor_schedule")

    return render_template("create_appointment.html")


# =====================================================
# DOCTOR SCHEDULE
# =====================================================

@app.route("/doctor_schedule")
def doctor_schedule():

    today = datetime.now().strftime("%Y-%m-%d")

    appointments = list(
        appointments_collection.find(
            {"doctor": session.get("user"), "date": today}
        )
    )

    return render_template("doctor_schedule.html", appointments=appointments, today=today)


# =====================================================
# PATIENT DASHBOARD (ONLY ONE ROUTE)
# =====================================================

@app.route("/patient")
def patient():

    if "user" not in session:
        return redirect("/")

    blocks = load_blocks()
    valid = verify_chain()

    return render_template("patient_home.html", blocks=blocks, valid=valid)


# =====================================================
# VIEW MEDICAL HISTORY
# =====================================================

@app.route("/medical_history")
def medical_history():

    if "user" not in session:
        return redirect("/")

    patient_id = session["user"]

    reports = list(reports_collection.find({"patient_id": patient_id}))

    history = []

    for r in reports:

        encrypted_data = base64.b64decode(r["encrypted_report"])
        decrypted_data = cipher.decrypt(encrypted_data)

        history.append({
            "report_name": r["report_name"],
            "uploaded_by": r["uploaded_by"],
            "hash": r["hash_key"]
        })

    return render_template("medical_history.html", history=history)


# =====================================================
# GRANT ACCESS
# =====================================================

@app.route("/grant_access", methods=["GET","POST"])
def grant_access():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        receiver = request.form["receiver"]

        share_text = f"{session['user']}-{receiver}"

        hash_key = hashlib.sha256(share_text.encode()).hexdigest()

        share_document = {

            "patient_id": session["user"],
            "shared_with": receiver,
            "hash_key": hash_key,
            "date": datetime.now().strftime("%Y-%m-%d")

        }

        shared_collection.insert_one(share_document)

        return render_template("grant_access.html",
                               message="Access Granted Successfully",
                               key=hash_key)

    return render_template("grant_access.html")


# =====================================================
# TRACK TREATMENT
# =====================================================

@app.route("/track_treatment")
def track_treatment():

    if "user" not in session:
        return redirect("/")

    patient_id = session["user"]

    treatments = list(treatments_collection.find({"patient_id": patient_id}))

    history = []

    for t in treatments:

        encrypted_data = base64.b64decode(t["encrypted_treatment"])
        decrypted_data = cipher.decrypt(encrypted_data)

        history.append({

            "doctor": t["doctor"],
            "treatment": decrypted_data.decode(),
            "date": t["date"],
            "hash": t["hash_key"]

        })

    return render_template("track_treatment.html", history=history)


# =====================================================
# ADMIN
# =====================================================

@app.route("/admin")
def admin():
    return render_template("admin.html")


# =====================================================
# INSURANCE
# =====================================================

@app.route("/insurance")
def insurance():

    blocks = load_blocks()
    valid = verify_chain()

    return render_template("insurance.html", blocks=blocks, valid=valid)


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
    app.run()
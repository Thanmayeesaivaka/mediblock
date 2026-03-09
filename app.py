from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
import hashlib
import base64

from database import add_user, find_user, load_blocks
from blockchain import create_block, verify_chain

app = Flask(__name__)
app.secret_key = "mediblock_secret"

# ---------------- MongoDB Atlas Connection ----------------

client = MongoClient(
"mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"
)

db = client["mediblock"]

patients_collection = db["patients"]
reports_collection = db["reports"]

# ---------------- Encryption Setup ----------------

# Generate once using Fernet.generate_key()
encryption_key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
cipher = Fernet(encryption_key)


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


# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    return render_template("admin.html")


# ---------------- DOCTOR DASHBOARD ----------------
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


# ---------------- VIEW PATIENT RECORDS ----------------
@app.route("/view_records")
def view_records():

    if "user" not in session:
        return redirect("/")

    patients = list(patients_collection.find())

    return render_template("view_records.html", patients=patients)


# ---------------- UPDATE TREATMENT ----------------
@app.route("/update_treatment", methods=["GET","POST"])
def update_treatment():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        patient = request.form["patient"]
        diagnosis = request.form["diagnosis"]
        prescription = request.form["prescription"]

        create_block(patient, session["user"], diagnosis, prescription)

        return redirect("/view_records")

    return render_template("update_treatment.html")


# =====================================================
# UPLOAD REPORT (AES + SHA256)
# =====================================================

@app.route("/upload_report", methods=["GET","POST"])
def upload_report():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        try:

            patient_id = request.form["pid"]
            file = request.files["report"]

            file_data = file.read()

            # SHA256 HASH
            hash_key = hashlib.sha256(file_data).hexdigest()

            # AES Encryption
            encrypted_data = cipher.encrypt(file_data)

            report_document = {

                "patient_id": patient_id,
                "report_name": file.filename,
                "encrypted_report": base64.b64encode(encrypted_data).decode(),
                "hash_key": hash_key,
                "uploaded_by": session["user"]

            }

            reports_collection.insert_one(report_document)

            return render_template(
                "upload_report.html",
                message="Report Encrypted and Stored Successfully"
            )

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("upload_report.html")


# ---------------- VIEW REPORTS ----------------
@app.route("/view_reports/<patient_id>")
def view_reports(patient_id):

    reports = reports_collection.find({"patient_id": patient_id})

    report_list = []

    for report in reports:

        encrypted_data = base64.b64decode(report["encrypted_report"])
        decrypted_data = cipher.decrypt(encrypted_data)

        report_list.append({
            "name": report["report_name"],
            "hash": report["hash_key"]
        })

    return render_template("view_reports.html", reports=report_list)


# ---------------- PATIENT ----------------
@app.route("/patient")
def patient():

    blocks = load_blocks()
    valid = verify_chain()

    return render_template("patient.html", blocks=blocks, valid=valid)


# ---------------- INSURANCE ----------------
@app.route("/insurance")
def insurance():

    blocks = load_blocks()
    valid = verify_chain()

    return render_template("insurance.html", blocks=blocks, valid=valid)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)
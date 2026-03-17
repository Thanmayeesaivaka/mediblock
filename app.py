from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
from bson import ObjectId
import base64

from database import add_user, find_user

app = Flask(__name__)
app.secret_key = "mediblock_secret"

# =====================================
# MongoDB CONNECTION
# =====================================

MONGO_URI = "mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["mediblock"]

patients_collection = db["patients"]
treatments_collection = db["treatments"]
reports_collection = db["reports"]
shared_collection = db["shared"]
claims_collection = db["claims"]
findings_collection = db["findings"]

# Check connection
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
    data = list(treatments_collection.find().limit(20))
    return render_template("view_records.html", data=data)


@app.route("/update_treatment", methods=["GET","POST"])
def update_treatment():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            text = f"Diagnosis:{request.form['diagnosis']}|Prescription:{request.form['prescription']}"
            enc = cipher.encrypt(text.encode())

            treatments_collection.insert_one({
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
        reports_collection.insert_one({
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
        shared_collection.insert_one({
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
    data = list(treatments_collection.find({"patient": session["user"]}).limit(20))
    return render_template("history.html", data=data)


@app.route("/grant_access", methods=["GET","POST"])
def grant_access():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        shared_collection.insert_one({
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


@app.route("/analyze_info")
def analyze_info():

    if "user" not in session:
        return redirect("/")

    data = list(reports_collection.find().limit(20))
    return render_template("analyze_info.html", data=data)


@app.route("/generate_reports")
def generate_reports():

    if "user" not in session:
        return redirect("/")

    treatments = list(treatments_collection.find().limit(50))

    disease_count = {}

    for t in treatments:
        try:
            encrypted_data = base64.b64decode(t["data"])
            decrypted_data = cipher.decrypt(encrypted_data).decode()

            disease = decrypted_data.split("|")[0].replace("Diagnosis:", "").strip()
            disease_count[disease] = disease_count.get(disease, 0) + 1
        except:
            continue

    labels = list(disease_count.keys()) or ["No Data"]
    values = list(disease_count.values()) or [1]

    return render_template("generate_reports.html", labels=labels, values=values)


@app.route("/submit_findings", methods=["GET","POST"])
def submit_findings():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        findings_collection.insert_one({
            "finding": request.form["finding"],
            "details": request.form["details"],
            "user": session["user"],
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


@app.route("/receive_claim", methods=["GET","POST"])
def receive_claim():

    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        claims_collection.insert_one({
            "claim_id": request.form["claim"],
            "patient": request.form["patient"],
            "amount": request.form["amount"],
            "status": "Pending"
        })

    return render_template("receive_claim.html")


@app.route("/validate_claim")
def validate_claim():

    if "user" not in session:
        return redirect("/")

    claims = list(claims_collection.find().limit(20))
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
# RUN
# =====================================

if __name__ == "__main__":
    app.run(debug=True)
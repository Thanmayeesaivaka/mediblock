from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime
import base64
import hashlib
import os

app = Flask(__name__)
app.secret_key = "mediblock_secret"

# ===============================
# MongoDB Connection
# ===============================
MONGO_URI = "mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["mediblock"]

patients_collection = db["patients"]
treatments_collection = db["treatments"]
reports_collection = db["reports"]
findings_collection = db["findings"]

# ===============================
# Encryption Key
# ===============================
key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
cipher = Fernet(key)

# ===============================
# HOME
# ===============================
@app.route("/")
def home():
    return render_template("main_home.html")

# ===============================
# LOGIN (FIXED)
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        username = request.form["username"]
        role = request.form["role"].strip().lower()   # ✅ FIX

        session["user"] = username
        session["role"] = role

        if role == "doctor":
            return redirect("/doctor")
        elif role == "patient":
            return redirect("/patient")
        elif role in ["research", "research analyst"]:
            return redirect("/research")

        return "Invalid Role"

    return render_template("login.html")

# ===============================
# DOCTOR MODULE
# ===============================
@app.route("/doctor")
def doctor():
    if "user" not in session:
        return redirect("/")
    return render_template("doctor.html")

# 🔹 Add Treatment
@app.route("/update_treatment", methods=["GET", "POST"])
def update_treatment():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        text = f"Diagnosis:{request.form['diagnosis']}|Prescription:{request.form['prescription']}"
        enc = cipher.encrypt(text.encode())

        treatments_collection.insert_one({
            "patient": request.form["patient"],
            "doctor": session["user"],
            "data": base64.b64encode(enc).decode(),
            "date": datetime.now().strftime("%Y-%m-%d")
        })

        return render_template("update_treatment.html", message="Added Successfully")

    return render_template("update_treatment.html")

# 🔹 Treatment History (Doctor)
@app.route("/treatment_history")
def treatment_history():
    if "user" not in session:
        return redirect("/")

    data = list(treatments_collection.find())

    history = []

    for t in data:
        try:
            encrypted_data = base64.b64decode(t["data"])
            decrypted = cipher.decrypt(encrypted_data).decode()

            hash_val = hashlib.sha256(decrypted.encode()).hexdigest()

            history.append({
                "patient": t["patient"],
                "doctor": t["doctor"],
                "decrypted": decrypted,
                "hash": hash_val
            })

        except:
            continue

    return render_template("treatment_history.html", history=history)

# ===============================
# PATIENT MODULE
# ===============================
@app.route("/patient")
def patient():
    if "user" not in session:
        return redirect("/")
    return render_template("patient.html")

# 🔹 Medical History (Reports)
@app.route("/medical_history")
def medical_history():
    if "user" not in session:
        return redirect("/")

    history = list(reports_collection.find({
        "patient": session["user"]
    }))

    return render_template("medical_history.html", history=history)

# 🔹 Track Treatment (DECRYPT + HASH)
@app.route("/track_treatment")
def track_treatment():
    if "user" not in session:
        return redirect("/")

    data = list(treatments_collection.find({
        "patient": session["user"]
    }))

    history = []

    for t in data:
        try:
            encrypted_data = base64.b64decode(t["data"])
            decrypted = cipher.decrypt(encrypted_data).decode()

            hash_val = hashlib.sha256(decrypted.encode()).hexdigest()

            history.append({
                "doctor": t["doctor"],
                "treatment": decrypted,
                "date": t["date"],
                "hash": hash_val
            })

        except:
            continue

    return render_template("track_treatment.html", history=history)

# ===============================
# RESEARCH MODULE
# ===============================
@app.route("/research")
def research():
    if "user" not in session:
        return redirect("/")
    return render_template("research.html")

# 🔹 Analyze Info
@app.route("/analyze_info")
def analyze_info():
    if "user" not in session:
        return redirect("/")

    data = list(findings_collection.find())

    return render_template("analyze_info.html", data=data)

# 🔹 Generate Reports (Charts)
@app.route("/generate_reports")
def generate_reports():
    if "user" not in session:
        return redirect("/")

    treatments = list(treatments_collection.find())

    disease_count = {}

    for t in treatments:
        try:
            encrypted_data = base64.b64decode(t["data"])
            decrypted = cipher.decrypt(encrypted_data).decode()

            disease = decrypted.split("|")[0].replace("Diagnosis:", "").strip()

            disease_count[disease] = disease_count.get(disease, 0) + 1

        except:
            continue

    labels = list(disease_count.keys())
    values = list(disease_count.values())

    return render_template("generate_reports.html", labels=labels, values=values)

# ===============================
# LOGOUT
# ===============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
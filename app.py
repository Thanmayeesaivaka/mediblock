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


    # ---------------- MongoDB ----------------

    client = MongoClient(
    "mongodb+srv://mediblock:mediblock123@cluster0.mvjq5vy.mongodb.net/mediblock?retryWrites=true&w=majority"
    )

    db = client["mediblock"]

    patients_collection = db["patients"]
    reports_collection = db["reports"]
    treatments_collection = db["treatments"]
    shared_collection = db["shared_data"]
    appointments_collection = db["appointments"]


    # ---------------- Encryption ----------------

    encryption_key = b'V2V1S0RjSndhT3R0d2FvV0t5QmZzQnFvTnNnQ1Z4bU8='
    cipher = Fernet(encryption_key)


    # ---------------- HOME ----------------
    @app.route("/")
    def home():
        return render_template("login.html")


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


    # ---------------- DOCTOR DASHBOARD ----------------
    @app.route("/doctor")
    def doctor():

        if "user" not in session:
            return redirect("/")

        return render_template("doctor.html")

    @app.route("/treatment_history")
    def treatment_history():

        if "user" not in session:
            return redirect("/")

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
    # DOCTOR DAILY SCHEDULE
    # =====================================================

    @app.route("/doctor_schedule")
    def doctor_schedule():

        if "user" not in session:
            return redirect("/")

        today = datetime.now().strftime("%Y-%m-%d")

        appointments = list(
            appointments_collection.find(
                {"doctor": session["user"], "date": today}
            )
        )

        return render_template(
            "doctor_schedule.html",
            appointments=appointments,
            today=today
        )


    # ---------------- LOGOUT ----------------
    @app.route("/logout")
    def logout():

        session.clear()

        return redirect("/")
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


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)


    # ---------------- RUN APP ----------------
    if __name__ == "__main__":
        app.run(debug=True)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import uuid
import qrcode
from datetime import datetime, timedelta
import math
import os
import io
import base64
import uuid
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app)

# ------------------ MongoDB ------------------

MONGO_URL = "mongodb+srv://attendify:Attendify%402026@attendify2026.87cn4pu.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URL)
db = client["attendance_system"]

faculty_col = db["faculty"]
sessions_col = db["sessions"]
attendance_col = db["attendance"]

# ------------------ Utils ------------------

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

# ------------------ Routes ------------------

@app.route("/")
def home():
    return "Attendify Backend Running"

# ------------------ Faculty Login ------------------

@app.route("/api/faculty/login", methods=["POST"])
def faculty_login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    print("LOGIN TRY:", email, password)

    user = faculty_col.find_one({"email": email, "password": password})

    print("FOUND USER:", user)

    if not user:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    return jsonify({
        "success": True,
        "faculty_id": str(user["_id"]),
        "name": user["name"]
    })

# ------------------ Create Session ------------------

@app.route("/api/session/create", methods=["POST"])
def create_session():
    try:
        data = request.json

        faculty_id = data.get("faculty_id")
        if not faculty_id:
            return jsonify({
                "success": False,
                "message": "Faculty not logged in"
            }), 401

        subject = data.get("subject")
        section = data.get("section")
        radius = float(data.get("radius"))
        time_limit = int(data.get("time_limit"))
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))

        token = str(uuid.uuid4())

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=time_limit)

        session = {
            "faculty_id": faculty_id,
            "subject": subject,
            "section": section,
            "radius": radius,
            "faculty_lat": lat,
            "faculty_lng": lng,
            "start_time": start_time,
            "end_time": end_time,
            "active": True,
            "token": token
        }

        result = sessions_col.insert_one(session)
        session_id = str(result.inserted_id)

        BASE_URL = "https://attendify26-production.up.railway.app"

        qr_url = f"{BASE_URL}/mark.html?session_id={session_id}&token={token}"

        img = qrcode.make(qr_url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            "success": True,
            "session_id": session_id,
            "token": token,
            "qr_url": qr_url,
            "qr_base64": qr_base64
        })

    except Exception as e:
        print("CREATE SESSION ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Server error"
        }), 500

# ------------------ Mark Attendance ------------------

@app.route("/api/attendance/mark", methods=["POST"])
def mark_attendance():
    data = request.json

    session_id = data.get("session_id")
    token = data.get("token")
    roll = data.get("roll")
    name = data.get("name")
    device_id = data.get("device_id")
    lat = float(data.get("lat"))
    lng = float(data.get("lng"))

    session = sessions_col.find_one({
        "_id": ObjectId(session_id),
        "token": token
    })

    if not session:
        return jsonify({"success": False, "message": "Invalid or expired session"}), 400

    now = datetime.utcnow()

    if now > session["end_time"]:
        return jsonify({"success": False, "message": "Time over"}), 400

    # Distance check
    dist = calculate_distance(
        lat, lng,
        session["faculty_lat"], session["faculty_lng"]
    )

    if dist > session["radius"]:
        return jsonify({"success": False, "message": "You are outside allowed area"}), 400

    # One roll = one attendance
    if attendance_col.find_one({"session_id": session_id, "roll": roll}):
        return jsonify({"success": False, "message": "Attendance already marked for this roll"}), 400

    # One device = one attendance
    if attendance_col.find_one({"session_id": session_id, "device_id": device_id}):
        return jsonify({"success": False, "message": "This device already used"}), 400

    attendance_col.insert_one({
        "session_id": session_id,
        "roll": roll,
        "name": name,
        "device_id": device_id,
        "time": now,
        "lat": lat,
        "lng": lng
    })

    return jsonify({"success": True, "message": "Attendance marked successfully"})

# ------------------ Serve Student Page ------------------

@app.route("/mark")
def mark_page():
    return send_from_directory("../frontend", "mark.html")

# ------------------ Serve QR Image Files ------------------

@app.route("/<path:filename>")
def serve_file(filename):
    return send_from_directory(os.getcwd(), filename)

# ------------------ Run Server ------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")




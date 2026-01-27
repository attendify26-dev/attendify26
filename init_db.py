from pymongo import MongoClient

# ------------------ MongoDB Connection ------------------

MONGO_URL = "mongodb+srv://attendify:Attendify%402026@attendify2026.87cn4pu.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URL)

db = client["attendance_system"]

faculty_col = db["faculty"]

# ------------------ Reset & Create Admin ------------------

print("Connecting to MongoDB...")

# Delete all existing faculty (to avoid confusion)
faculty_col.delete_many({})

# Insert fresh admin user
admin_user = {
    "name": "Admin",
    "email": "admin@college.com",
    "password": "admin123"
}

faculty_col.insert_one(admin_user)

print("✅ Admin user created successfully!")
print("Login credentials:")
print("Email: admin@college.com")
print("Password: admin123")

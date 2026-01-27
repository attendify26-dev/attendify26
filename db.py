from pymongo import MongoClient

MONGO_URL = "mongodb+srv://attendify:Attendify%402026@attendify2026.87cn4pu.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URL)

db = client["attendance_system"]

print("MongoDB Connected Successfully")

import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

# Define paths precisely based on project structure
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DIST_DIR = os.path.join(ROOT_DIR, "dist")

app = Flask(__name__, static_folder=DIST_DIR, static_url_path="")
CORS(app)

# MongoDB Connection with error handling
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:Password123@cluster0.cx7lsrw.mongodb.net/moms_kitchen?retryWrites=true&w=majority")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.get_database()
    users_collection = db.users
    client.server_info()
    print("✅ Connected successfully to MongoDB Atlas!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

@app.route("/api/signin", methods=["POST"])
def signin():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = users_collection.find_one({"email": email, "password": password})
        if user:
            return jsonify({"success": True, "message": "Login successful", "email": user["email"]})
        else:
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        if users_collection.find_one({"email": email}):
            return jsonify({"error": "User already exists"}), 400

        users_collection.insert_one({"email": email, "password": password})
        return jsonify({"success": True, "message": "Signup successful"})
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

# Explicit routes to handle static assets and SPA client-side routing
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
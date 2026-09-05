import os
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__, static_folder="../dist", static_url_path="")
CORS(app)

# MongoDB Connection using environment variable or fallback URI
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:Password123@cluster0.cx7lsrw.mongodb.net/moms_kitchen?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db = client.get_database()
users_collection = db.users

@app.route("/api/signin", methods=["POST"])
def signin():
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

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    users_collection.insert_one({"email": email, "password": password})
    return jsonify({"success": True, "message": "Signup successful"})

# Dynamic fallback route to serve React frontend SPA
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

from a2wsgi import ASGIMiddleware
asgi_app = ASGIMiddleware(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
import os
from flask import Flask, send_from_directory, jsonify, request, send_file
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from a2wsgi import WSGIMiddleware

# Get absolute path of the project root and dist folder
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DIST_DIR = os.path.join(BASE_DIR, 'dist')

app = Flask(__name__, static_folder=DIST_DIR, static_url_path='')
CORS(app)

# MongoDB Atlas Connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://admin:Password123@cluster0.cx7lsrw.mongodb.net/moms_kitchen?retryWrites=true&w=majority')
client = MongoClient(MONGO_URI)
db = client['moms_kitchen']

# --- API AUTHENTICATION ROUTES ---
@app.route('/api/signin', methods=['POST'])
def signin():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    
    user = db['users'].find_one({'email': email})
    if user or email:
        return jsonify({"success": True, "message": "Sign in successful!", "email": email}), 200
    return jsonify({"success": False, "error": "User not found"}), 404

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    
    existing_user = db['users'].find_one({'email': email})
    if existing_user:
        return jsonify({"success": False, "error": "User already exists"}), 400
        
    db['users'].insert_one({'email': email, 'password': password, 'createdAt': datetime.utcnow()})
    return jsonify({"success": True, "message": "Account created successfully!"}), 201

# --- API ORDERS ROUTES ---
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json or {}
    data['createdAt'] = datetime.utcnow()
    data['status'] = "Order Placed"
    db['orders'].insert_one(data)
    return jsonify({"success": True, "message": "Order created successfully!"}), 201

@app.route('/api/orders/user/<email>', methods=['GET'])
def get_user_orders(email):
    orders = list(db['orders'].find({'userEmail': email}, {'_id': False}))
    return jsonify(orders), 200

@app.route('/api/orders/cancel/<order_id>', methods=['PUT'])
def cancel_order(order_id):
    db['orders'].update_one({'id': order_id}, {'$set': {'status': 'Cancelled'}})
    return jsonify({"success": True, "message": "Order cancelled"}), 200

# --- ADMIN ROUTES ---
@app.route('/api/admin/orders', methods=['GET'])
def admin_get_orders():
    orders = list(db['orders'].find({}))
    for o in orders:
        o['_id'] = str(o['_id'])
    return jsonify(orders), 200

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    users = list(db['users'].find({}))
    for u in users:
        u['_id'] = str(u['_id'])
    return jsonify(users), 200

@app.route('/api/admin/orders/update/<order_id>', methods=['PUT'])
def admin_update_order(order_id):
    data = request.json or {}
    update_fields = {}
    if 'status' in data:
        update_fields['status'] = data['status']
    if 'deliveryTime' in data:
        update_fields['deliveryTime'] = data['deliveryTime']
        
    db['orders'].update_one({'id': order_id}, {'$set': update_fields})
    return jsonify({"success": True, "message": "Order updated"}), 200

@app.route('/api/admin/signin', methods=['POST'])
def admin_signin():
    data = request.json or {}
    email = data.get('email')
    return jsonify({"success": True, "message": "Admin signed in", "email": email}), 200

@app.route('/api/admin/signup', methods=['POST'])
def admin_signup():
    data = request.json or {}
    email = data.get('email')
    return jsonify({"success": True, "message": "Admin registered successfully", "email": email}), 201

# --- SERVE REACT FRONTEND & SPA CATCH-ALL ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
        
    requested_file = os.path.join(DIST_DIR, path)
    if path != "" and os.path.exists(requested_file):
        return send_from_directory(DIST_DIR, path)
    else:
        return send_file(os.path.join(DIST_DIR, 'index.html'))

@app.errorhandler(404)
def not_found(e):
    return send_file(os.path.join(DIST_DIR, 'index.html'))

# Wrap the Flask app using a2wsgi for Uvicorn compatibility
asgi_app = WSGIMiddleware(app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
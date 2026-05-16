from flask import Blueprint, request, jsonify
from src.models.user import User
from src.middleware.auth import generate_token

login_bp = Blueprint("login", __name__)

@login_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        token = generate_token(str(user.id))
        return jsonify({"token": token})
    return jsonify({"error": "Invalid credentials"}), 401

@login_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    user = User.create(data)
    return jsonify({"id": user.id}), 201

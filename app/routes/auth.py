# app/routes/auth.py
from flask import Blueprint, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, Users

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth_bp.post("/signup")
def signup():
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "username and password required"}, 400

    if Users.query.filter_by(username=username).first():
        return {"error": "username already taken"}, 409

    user = Users(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return {"id": user.id, "username": user.username}, 201

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "username and password required"}, 400

    user = Users.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return {"error": "invalid credentials"}, 401

    session["user_id"] = user.id
    return {"id": user.id, "username": user.username}, 200

@auth_bp.post("/logout")
def logout():
    session.clear()
    return "", 204
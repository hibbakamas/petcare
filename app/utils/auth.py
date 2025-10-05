# app/utils/auth.py
from functools import wraps
from flask import session, jsonify

def login_required_api(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify(error="authentication required"), 401
        return fn(*args, **kwargs)
    return wrapper
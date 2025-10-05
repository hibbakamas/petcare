from flask import Blueprint, redirect, url_for, session

home_ui = Blueprint("home_ui", __name__)

@home_ui.get("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("households_ui.households_index"))
    return redirect(url_for("auth_ui.login_get"))
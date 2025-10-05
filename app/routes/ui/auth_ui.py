from flask import Blueprint, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from ...models import db, Users

auth_ui = Blueprint("auth_ui", __name__)

@auth_ui.get("/login")
def login_get():
    return render_template("login.html")

@auth_ui.post("/login")
def login_post():
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    if not username or not password:
        return render_template("login.html", error="Please fill in both fields."), 400

    user = db.session.query(Users).filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template("login.html", error="Invalid username or password."), 401

    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("households_ui.households_index"))

@auth_ui.get("/signup")
def signup_get():
    return render_template("signup.html")

@auth_ui.post("/signup")
def signup_post():
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    if not username or not password:
        return render_template("signup.html", error="Please fill in both fields."), 400

    if db.session.query(Users).filter_by(username=username).first():
        return render_template("signup.html", error="That username is taken."), 409

    user = Users(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("households_ui.households_index"))

# keep ONLY this:
@auth_ui.get("/logout")
def logout_get():
    session.clear()
    return redirect(url_for("auth_ui.login_get"))
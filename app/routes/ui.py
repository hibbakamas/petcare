from flask import Blueprint, render_template, redirect, url_for, request, session
from sqlalchemy.exc import NoResultFound, IntegrityError
from ..models import db, Users

ui = Blueprint("ui", __name__)

# home: if logged in go to households, otherwise to login
@ui.get("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("ui.households_index"))
    return redirect(url_for("ui.login_get"))

# authentication
@ui.get("/login")
def login_get():
    return render_template("login.html")

@ui.post("/login")
def login_post():
    username = request.form.get("username", "").strip()

    if not username:
        return render_template("login.html", error="Username is required.")

    try:
        user = db.session.query(Users).filter_by(username=username).one()
    except NoResultFound:
        return render_template("login.html", error="User not found. Please sign up first.")

    # remember the user
    session["user_id"] = user.id
    session["username"] = user.username
    # go to households hub (join / create / open)
    return redirect(url_for("ui.households_index"))

@ui.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("ui.login_get"))

@ui.get("/signup")
def signup_get():
    return render_template("signup.html")

@ui.post("/signup")
def signup_post():
    username = request.form.get("username", "").strip()
    if not username:
        return render_template("signup.html", error="Username is required.")

    # simple uniqueness check (no IntegrityError required)
    if db.session.query(Users).filter_by(username=username).first():
        return render_template("signup.html", error="Username is already taken.")

    user = Users(username=username, password_hash="")  # keeping blank for now
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("ui.login_get"))

@ui.get("/households/<int:household_id>")
def household_dashboard(household_id):
    return render_template("households_show.html", household_id=household_id)

@ui.get("/households")
def households_index():
    # later we’ll load this user’s households from the DB
    return render_template("households_index.html")


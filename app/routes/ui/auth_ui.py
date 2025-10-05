"""UI Auth routes (server-rendered).

Handles login, signup, and logout for the HTML UI.
Uses session cookies; errors render the same template with a message.
"""

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ...models import Users, db

auth_ui = Blueprint("auth_ui", __name__)


@auth_ui.get("/login")
def login_get():
    """Render login form."""
    return render_template("login.html")


@auth_ui.post("/login")
def login_post():
    """Process login form and start a session."""
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()

    if not username or not password:
        # 400 to indicate a client-side form error
        return render_template("login.html", error="Please fill in both fields."), 400

    user = db.session.query(Users).filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        # 401 for invalid credentials
        return render_template("login.html", error="Invalid username or password."), 401

    # Store minimal identity in the session
    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("households_ui.households_index"))


@auth_ui.get("/signup")
def signup_get():
    """Render signup form."""
    return render_template("signup.html")


@auth_ui.post("/signup")
def signup_post():
    """Create a new user from the signup form and start a session."""
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()

    if not username or not password:
        return render_template("signup.html", error="Please fill in both fields."), 400

    if db.session.query(Users).filter_by(username=username).first():
        # 409 for conflict (username already taken)
        return render_template("signup.html", error="That username is taken."), 409

    user = Users(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("households_ui.households_index"))


@auth_ui.get("/logout")
def logout_get():
    """Clear the session and send the user back to login."""
    session.clear()
    return redirect(url_for("auth_ui.login_get"))

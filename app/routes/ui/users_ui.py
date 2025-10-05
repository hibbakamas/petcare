from flask import Blueprint, render_template, redirect, url_for, request, session
from sqlalchemy.exc import IntegrityError
from ...models import db, Users, HouseholdMember

users_ui = Blueprint("users_ui", __name__)

@users_ui.get("/profile")
def profile_get():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth_ui.login_get"))

    user = db.session.get(Users, user_id)
    memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
    return render_template("profile.html", user=user, memberships=memberships)

@users_ui.post("/profile/username")
def profile_update_username():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth_ui.login_get"))

    new_username = (request.form.get("username") or "").strip()
    if not new_username:
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               username_error="Username cannot be empty.")

    if db.session.query(Users).filter(Users.username == new_username, Users.id != user_id).first():
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               username_error="That username is already taken.")

    user = db.session.get(Users, user_id)
    user.username = new_username
    db.session.commit()
    session["username"] = new_username
    return redirect(url_for("users_ui.profile_get"))

@users_ui.post("/households/<int:household_id>/nickname")
def profile_update_nickname(household_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth_ui.login_get"))

    new_nick = (request.form.get("nickname") or "").strip()
    if not new_nick:
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               nickname_errors={household_id: "Nickname cannot be empty."})

    m = db.session.query(HouseholdMember).filter_by(user_id=user_id, household_id=household_id).first()
    if not m:
        return redirect(url_for("users_ui.profile_get"))

    m.nickname = new_nick
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               nickname_errors={household_id: "That nickname is already used in this household."})

    return redirect(url_for("users_ui.profile_get"))
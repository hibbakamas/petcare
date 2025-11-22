"""UI routes for user profile: view profile, update username, update household nickname."""

from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from ...models import HouseholdMember, Users, db
from app.utils.auth import login_required_ui

users_ui = Blueprint("users_ui", __name__)


@users_ui.get("/profile")
@login_required_ui
def profile_get():
    """Render the profile page with memberships."""
    user_id = session["user_id"]
    user = db.session.get(Users, user_id)
    memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
    return render_template("profile.html", user=user, memberships=memberships)


@users_ui.post("/profile/username")
@login_required_ui
def profile_update_username():
    """Update the current user's username."""
    user_id = session["user_id"]

    new_username = (request.form.get("username") or "").strip()
    if not new_username:
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template(
            "profile.html",
            user=user,
            memberships=memberships,
            username_error="Username cannot be empty.",
        )

    # Reject if another user already has this username.
    taken = (
        db.session.query(Users)
        .filter(Users.username == new_username, Users.id != user_id)
        .first()
    )
    if taken:
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template(
            "profile.html",
            user=user,
            memberships=memberships,
            username_error="That username is already taken.",
        )

    user = db.session.get(Users, user_id)
    user.username = new_username
    db.session.commit()
    session["username"] = new_username
    return redirect(url_for("users_ui.profile_get"))


@users_ui.post("/households/<int:household_id>/nickname")
@login_required_ui
def profile_update_nickname(household_id: int):
    """Update the member nickname for a specific household."""
    user_id = session["user_id"]

    new_nick = (request.form.get("nickname") or "").strip()
    if not new_nick:
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template(
            "profile.html",
            user=user,
            memberships=memberships,
            nickname_errors={household_id: "Nickname cannot be empty."},
        )

    m = (
        db.session.query(HouseholdMember)
        .filter_by(user_id=user_id, household_id=household_id)
        .first()
    )
    if not m:
        return redirect(url_for("users_ui.profile_get"))

    m.nickname = new_nick
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template(
            "profile.html",
            user=user,
            memberships=memberships,
            nickname_errors={
                household_id: "That nickname is already used in this household."
            },
        )

    return redirect(url_for("users_ui.profile_get"))
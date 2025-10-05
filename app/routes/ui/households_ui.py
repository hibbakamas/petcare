"""UI routes for households: list/join/create/leave and dashboard."""

import random

from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from ...models import Household, HouseholdMember, db

households_ui = Blueprint("households_ui", __name__)


def _gen_code(n: int = 6) -> str:
    """Generate a readable join code (no ambiguous chars)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))


@households_ui.get("/households")
def households_index():
    """List the current user's household memberships."""
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth_ui.login_get"))

    memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
    return render_template("households_index.html", memberships=memberships)


@households_ui.get("/households/new")
def households_new_get():
    """Render the new-household form."""
    if not session.get("user_id"):
        return redirect(url_for("auth_ui.login_get"))
    return render_template("households_new.html")


@households_ui.post("/households/new")
def households_new_post():
    """Create a new household and add the current user as a member."""
    if not session.get("user_id"):
        return redirect(url_for("auth_ui.login_get"))

    name = (request.form.get("name", "")).strip()
    nickname = (
        request.form.get("nickname", "") or session.get("username", "") or "Owner"
    ).strip()

    if not name:
        return render_template(
            "households_new.html", error="Household name is required."
        )

    # Generate a unique join code.
    code = _gen_code()
    while db.session.query(Household).filter_by(join_code=code).first():
        code = _gen_code()

    h = Household(name=name, join_code=code)
    db.session.add(h)
    db.session.commit()

    # Add creator as a member; nickname must be unique per household.
    m = HouseholdMember(
        user_id=session["user_id"], household_id=h.id, nickname=nickname or "Owner"
    )
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        m = HouseholdMember(
            user_id=session["user_id"],
            household_id=h.id,
            nickname=f"{nickname or 'Owner'} (owner)",
        )
        db.session.add(m)
        db.session.commit()

    return redirect(url_for("households_ui.household_dashboard", household_id=h.id))


@households_ui.get("/join")
def join_get():
    """Render the join-household form."""
    if not session.get("user_id"):
        return redirect(url_for("auth_ui.login_get"))
    return render_template("join.html")


@households_ui.post("/join")
def join_post():
    """Join a household by code; handle nickname uniqueness."""
    if not session.get("user_id"):
        return redirect(url_for("auth_ui.login_get"))

    code = (request.form.get("code", "")).strip().upper()
    nickname = (
        request.form.get("nickname", "") or session.get("username", "") or ""
    ).strip()

    if not code:
        return render_template("join.html", error="Join code is required.")

    h = db.session.query(Household).filter_by(join_code=code).first()
    if not h:
        return render_template(
            "join.html", error="Invalid join code. Please try again."
        )

    existing = (
        db.session.query(HouseholdMember)
        .filter_by(user_id=session["user_id"], household_id=h.id)
        .first()
    )
    if existing:
        return render_template(
            "join.html",
            error="You’re already a member of this household.",
            existing_household=h,
        )

    if not nickname:
        nickname = session.get("username", "Member")

    m = HouseholdMember(
        user_id=session["user_id"], household_id=h.id, nickname=nickname
    )
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template(
            "join.html", error="Nickname already in use in this household. Try another."
        )

    return redirect(url_for("households_ui.household_dashboard", household_id=h.id))


@households_ui.post("/households/<int:household_id>/leave")
def households_leave(household_id: int):
    """Leave a household the user belongs to."""
    if not session.get("user_id"):
        return redirect(url_for("auth_ui.login_get"))

    m = (
        db.session.query(HouseholdMember)
        .filter_by(user_id=session["user_id"], household_id=household_id)
        .first()
    )
    if not m:
        return render_template("errors/404.html"), 404

    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("households_ui.households_index"))


@households_ui.get("/households/<int:household_id>")
def household_dashboard(household_id: int):
    """Show a household dashboard with pets and members."""
    if not session.get("user_id"):
        return redirect(url_for("auth_ui.login_get"))

    h = db.session.get(Household, household_id)
    if not h:
        return render_template("errors/404.html"), 404

    pets = h.pets
    members = h.members
    return render_template(
        "households_show.html", household=h, pets=pets, members=members
    )

# app/routes/ui/households_ui.py
"""UI routes for households: list/join/create/leave and dashboard."""

from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from ...models import Household, HouseholdMember, db
from app.utils.join_code import gen_join_code
from app.utils.auth import login_required_ui

households_ui = Blueprint("households_ui", __name__)


@households_ui.get("/households")
@login_required_ui
def households_index():
    """List the current user's household memberships."""
    user_id = session["user_id"]
    memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
    return render_template("households_index.html", memberships=memberships)


@households_ui.get("/households/new")
@login_required_ui
def households_new_get():
    """Render the new-household form."""
    return render_template("households_new.html")


@households_ui.post("/households/new")
@login_required_ui
def households_new_post():
    """Create a new household and add the current user as a member."""
    name = (request.form.get("name", "")).strip()
    nickname = (
        request.form.get("nickname", "") or session.get("username", "") or "Owner"
    ).strip()

    if not name:
        return render_template(
            "households_new.html", error="Household name is required."
        )

    # Generate a unique join code.
    code = gen_join_code()
    while db.session.query(Household).filter_by(join_code=code).first():
        code = gen_join_code()

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
@login_required_ui
def join_get():
    """Render the join-household form."""
    return render_template("join.html")


@households_ui.post("/join")
@login_required_ui
def join_post():
    """Join a household by code; handle nickname uniqueness."""
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
@login_required_ui
def households_leave(household_id: int):
    """Leave a household the user belongs to."""
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
@login_required_ui
def household_dashboard(household_id: int):
    """Show a household dashboard with pets and members."""
    h = db.session.get(Household, household_id)
    if not h:
        return render_template("errors/404.html"), 404

    pets = h.pets
    members = h.members
    return render_template(
        "households_show.html", household=h, pets=pets, members=members
    )
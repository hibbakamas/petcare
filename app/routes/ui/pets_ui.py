"""UI routes for pets: create, delete, and detail view with entry filters."""

from datetime import datetime, time, timedelta

from flask import Blueprint, redirect, render_template, request, url_for
from sqlalchemy import desc

from ...models import Entry, Pet, db

pets_ui = Blueprint("pets_ui", __name__)


@pets_ui.get("/households/<int:household_id>/pets/new")
def pets_new_get(household_id: int):
    """Render the new-pet form."""
    return render_template("pets_new.html", household_id=household_id)


@pets_ui.post("/households/<int:household_id>/pets/new")
def pets_new_post(household_id: int):
    """Create a new pet in the given household."""
    name = (request.form.get("name", "")).strip()
    if not name:
        return render_template(
            "pets_new.html", household_id=household_id, error="Pet name is required."
        )

    p = Pet(household_id=household_id, name=name)
    db.session.add(p)
    db.session.commit()
    return redirect(
        url_for("households_ui.household_dashboard", household_id=household_id)
    )


@pets_ui.post("/households/<int:household_id>/pets/<int:pet_id>/delete")
def pets_delete(household_id: int, pet_id: int):
    """Delete a pet if it belongs to the specified household."""
    p = db.session.get(Pet, pet_id)
    if not p or p.household_id != household_id:
        return render_template("errors/404.html"), 404

    db.session.delete(p)
    db.session.commit()
    return redirect(
        url_for("households_ui.household_dashboard", household_id=household_id)
    )


@pets_ui.get("/pets/<int:pet_id>")
def pets_show(pet_id: int):
    """Show a pet detail page with entries filtered by range."""
    pet = db.session.get(Pet, pet_id)
    if not pet:
        return render_template("errors/404.html"), 404

    rng = (request.args.get("range") or "today").lower()
    now = datetime.utcnow()
    today = now.date()

    # Compute start time for the requested range; default to "today".
    if rng in ("today", "daily", "day"):
        start = datetime.combine(today, time.min)
        rng = "today"
    elif rng == "week":
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, time.min)
    elif rng == "month":
        first = today.replace(day=1)
        start = datetime.combine(first, time.min)
    elif rng == "all":
        start = None
    else:
        start = datetime.combine(today, time.min)
        rng = "today"

    q = db.session.query(Entry).filter(Entry.pet_id == pet_id)
    if start:
        q = q.filter(Entry.created_at >= start)
    entries = q.order_by(desc(Entry.created_at)).all()

    # Map user_id -> nickname for display.
    members_map = {m.user_id: m.nickname for m in pet.household.members}

    return render_template(
        "pets_show.html", pet=pet, entries=entries, range=rng, members_map=members_map
    )

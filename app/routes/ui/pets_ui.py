from flask import Blueprint, render_template, redirect, url_for, request, session
from sqlalchemy import desc
from datetime import datetime, timedelta, time
from ...models import db, Pet, Entry

pets_ui = Blueprint("pets_ui", __name__)

@pets_ui.get("/households/<int:household_id>/pets/new")
def pets_new_get(household_id):
    return render_template("pets_new.html", household_id=household_id)

@pets_ui.post("/households/<int:household_id>/pets/new")
def pets_new_post(household_id):
    name = request.form.get("name", "").strip()
    if not name:
        return render_template("pets_new.html", household_id=household_id, error="Pet name is required.")
    p = Pet(household_id=household_id, name=name)
    db.session.add(p)
    db.session.commit()
    return redirect(url_for("households_ui.household_dashboard", household_id=household_id))

@pets_ui.post("/households/<int:household_id>/pets/<int:pet_id>/delete")
def pets_delete(household_id, pet_id):
    p = db.session.get(Pet, pet_id)
    if not p or p.household_id != household_id:
        return render_template("errors/404.html"), 404
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("households_ui.household_dashboard", household_id=household_id))

@pets_ui.get("/pets/<int:pet_id>")
def pets_show(pet_id):
    pet = db.session.get(Pet, pet_id)
    if not pet:
        return render_template("errors/404.html"), 404

    rng = (request.args.get("range") or "today").lower()
    now = datetime.utcnow()
    today = now.date()

    if rng in ("today", "daily", "day"):
        start = datetime.combine(today, time.min); rng = "today"
    elif rng == "week":
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, time.min)
    elif rng == "month":
        first = today.replace(day=1)
        start = datetime.combine(first, time.min)
    elif rng == "all":
        start = None
    else:
        start = datetime.combine(today, time.min); rng = "today"

    q = db.session.query(Entry).filter(Entry.pet_id == pet_id)
    if start:
        q = q.filter(Entry.created_at >= start)
    entries = q.order_by(desc(Entry.created_at)).all()

    members_map = {m.user_id: m.nickname for m in pet.household.members}

    return render_template("pets_show.html", pet=pet, entries=entries, range=rng, members_map=members_map)
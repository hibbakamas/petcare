from flask import Blueprint, render_template, redirect, url_for, request, session
from ...models import db, Entry, Pet
from sqlalchemy import desc

entries_ui = Blueprint("entries_ui", __name__)

@entries_ui.post("/pets/<int:pet_id>/entries/new")
def entries_create(pet_id):
    pet = db.session.get(Pet, pet_id)
    if not pet:
        return render_template("errors/404.html"), 404

    content = (request.form.get("content") or "").strip()
    if not content:
        return render_template(
            "pets_show.html",
            pet=pet,
            entries=db.session.query(Entry).filter_by(pet_id=pet_id).order_by(desc(Entry.created_at)).all(),
            range="day",
            error="Entry text is required."
        )

    e = Entry(pet_id=pet_id, user_id=session["user_id"], content=content)
    db.session.add(e)
    db.session.commit()
    return redirect(url_for("pets_ui.pets_show", pet_id=pet_id))

@entries_ui.post("/pets/<int:pet_id>/entries/<int:entry_id>/delete")
def entries_delete(pet_id, entry_id):
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    db.session.delete(e)
    db.session.commit()
    return redirect(url_for("pets_ui.pets_show", pet_id=pet_id))

@entries_ui.get("/pets/<int:pet_id>/entries/<int:entry_id>/edit")
def entries_edit_get(pet_id, entry_id):
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    return render_template("entries_edit.html", pet_id=pet_id, entry=e)

@entries_ui.post("/pets/<int:pet_id>/entries/<int:entry_id>/edit")
def entries_edit_post(pet_id, entry_id):
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    content = (request.form.get("content") or "").strip()
    if not content:
        return render_template("entries_edit.html", pet_id=pet_id, entry=e, error="Content cannot be empty.")

    e.content = content
    db.session.commit()
    return redirect(url_for("pets_ui.pets_show", pet_id=pet_id))
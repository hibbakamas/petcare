"""UI routes for pet entries (create, edit, delete).

Server-rendered views that use the session for identity and show templates with
inline error messages when validation fails.
"""

from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import desc

from ...models import Entry, Pet, db

entries_ui = Blueprint("entries_ui", __name__)


@entries_ui.post("/pets/<int:pet_id>/entries/new")
def entries_create(pet_id: int):
    """Create a new entry for a pet; render form errors on the same page."""
    pet = db.session.get(Pet, pet_id)
    if not pet:
        return render_template("errors/404.html"), 404

    content = (request.form.get("content") or "").strip()
    if not content:
        # Re-render the pet page with an error and existing entries
        entries = (
            db.session.query(Entry)
            .filter_by(pet_id=pet_id)
            .order_by(desc(Entry.created_at))
            .all()
        )
        return render_template(
            "pets_show.html",
            pet=pet,
            entries=entries,
            range="day",
            error="Entry text is required.",
        )

    e = Entry(pet_id=pet_id, user_id=session["user_id"], content=content)
    db.session.add(e)
    db.session.commit()
    return redirect(url_for("pets_ui.pets_show", pet_id=pet_id))


@entries_ui.post("/pets/<int:pet_id>/entries/<int:entry_id>/delete")
def entries_delete(pet_id: int, entry_id: int):
    """Delete an entry (author-only)."""
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    db.session.delete(e)
    db.session.commit()
    return redirect(url_for("pets_ui.pets_show", pet_id=pet_id))


@entries_ui.get("/pets/<int:pet_id>/entries/<int:entry_id>/edit")
def entries_edit_get(pet_id: int, entry_id: int):
    """Render the edit form for an entry (author-only)."""
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    return render_template("entries_edit.html", pet_id=pet_id, entry=e)


@entries_ui.post("/pets/<int:pet_id>/entries/<int:entry_id>/edit")
def entries_edit_post(pet_id: int, entry_id: int):
    """Process the edit form for an entry (author-only)."""
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    content = (request.form.get("content") or "").strip()
    if not content:
        return render_template(
            "entries_edit.html",
            pet_id=pet_id,
            entry=e,
            error="Content cannot be empty.",
        )

    e.content = content
    db.session.commit()
    return redirect(url_for("pets_ui.pets_show", pet_id=pet_id))

# entry endpoints (notes/logs for a pet)

from flask import Blueprint, request, session
from ..models import db, Entry, Pet, Users

entries_bp = Blueprint("entries", __name__, url_prefix="/api/v1")

@entries_bp.post("/pets/<int:pet_id>/entries")
def create_entry(pet_id):
    Pet.query.get_or_404(pet_id)

    data = request.get_json()
    content = data.get("content")

    if not content:
        return {"error": "content is required"}, 400

    e = Entry(
        pet_id=pet_id,
        user_id=session["user_id"],
        content=content
    )
    db.session.add(e)
    db.session.commit()

    body = {
        "id": e.id,
        "pet_id": e.pet_id,
        "user_id": e.user_id,
        "content": e.content,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }
    return body, 201, {"Location": f"/api/v1/entries/{e.id}"}

# list entries for a pet (newest first)
@entries_bp.get("/pets/<int:pet_id>/entries")
def list_entries(pet_id):
    Pet.query.get_or_404(pet_id)
    rows = Entry.query.filter_by(pet_id=pet_id).order_by(Entry.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "pet_id": e.pet_id,
            "user_id": e.user_id,
            "content": e.content,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in rows
    ], 200

# get a single entry
@entries_bp.get("/entries/<int:entry_id>")
def get_entry(entry_id):
    e = Entry.query.get_or_404(entry_id)
    return {
        "id": e.id,
        "pet_id": e.pet_id,
        "user_id": e.user_id,
        "content": e.content,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }, 200

@entries_bp.patch("/entries/<int:entry_id>")
def patch_entry(entry_id):
    e = Entry.query.get_or_404(entry_id)
    data = request.get_json() or {}
    if "content" not in data or not data["content"]:
        return {"error": "content is required"}, 400

    e.content = data["content"]
    db.session.commit()
    return {
        "id": e.id,
        "pet_id": e.pet_id,
        "user_id": e.user_id,
        "content": e.content,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }, 200

@entries_bp.delete("/entries/<int:entry_id>")
def delete_entry(entry_id):
    e = Entry.query.get_or_404(entry_id)
    db.session.delete(e)
    db.session.commit()
    return "", 204

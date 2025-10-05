# app/routes/api/entries.py
# entry endpoints (notes/logs for a pet)

from flask import Blueprint, request, session, jsonify
from ...models import db, Entry, Pet
from app.utils.auth import login_required_api  # <-- add this

entries_bp = Blueprint("entries", __name__, url_prefix="/api/v1")

def _json_error(msg, status):  # tiny helper for consistency
    return jsonify(error=msg), status

@entries_bp.post("/pets/<int:pet_id>/entries")
@login_required_api
def create_entry(pet_id):
    # 404 if pet doesn't exist
    Pet.query.get_or_404(pet_id)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return _json_error("content is required", 400)

    e = Entry(
        pet_id=pet_id,
        user_id=session["user_id"],  # guaranteed by decorator
        content=content,
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
@login_required_api  # optional, but keeps API consistent with session auth
def list_entries(pet_id):
    Pet.query.get_or_404(pet_id)
    rows = (Entry.query
            .filter_by(pet_id=pet_id)
            .order_by(Entry.created_at.desc())
            .all())
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
@login_required_api  # optional; add/remove based on your policy
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
@login_required_api
def patch_entry(entry_id):
    e = Entry.query.get_or_404(entry_id)

    # Author-only edit (match your UI rule)
    if e.user_id != session.get("user_id"):
        return _json_error("forbidden", 403)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return _json_error("content is required", 400)

    e.content = content
    db.session.commit()
    return {
        "id": e.id,
        "pet_id": e.pet_id,
        "user_id": e.user_id,
        "content": e.content,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }, 200

@entries_bp.delete("/entries/<int:entry_id>")
@login_required_api
def delete_entry(entry_id):
    e = Entry.query.get_or_404(entry_id)

    # Author-only delete
    if e.user_id != session.get("user_id"):
        return _json_error("forbidden", 403)

    db.session.delete(e)
    db.session.commit()
    return "", 204
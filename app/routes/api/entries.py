"""Entries API: create, list, read, update, and delete pet entries (notes/logs).

Session-based auth is required for all endpoints. Responses use a minimal,
consistent JSON shape and standard status codes.
"""

from flask import Blueprint, request, session

from app.utils.auth import login_required_api

from ...models import Entry, Pet, db
from .helpers import json_error as _json_error  # shared JSON error helper

entries_bp = Blueprint("entries", __name__, url_prefix="/api/v1")


@entries_bp.post("/pets/<int:pet_id>/entries")
@login_required_api
def create_entry(pet_id: int):
    """Create an entry for a pet (author = current user).

    Returns:
        201 with {id, pet_id, user_id, content, created_at} and Location header
        400 if content is missing/blank
        404 if the pet does not exist
    """
    # 404 if pet doesn't exist
    Pet.query.get_or_404(pet_id)

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return _json_error("content is required", 400)

    e = Entry(
        pet_id=pet_id,
        user_id=session["user_id"],  # guaranteed by @login_required_api
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


@entries_bp.get("/pets/<int:pet_id>/entries")
@login_required_api
def list_entries(pet_id: int):
    """List entries for a pet (newest first).

    Returns:
        200 with a JSON array of entries
        404 if the pet does not exist
    """
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


@entries_bp.get("/entries/<int:entry_id>")
@login_required_api
def get_entry(entry_id: int):
    """Fetch a single entry by id.

    Returns:
        200 with entry JSON
        404 if the entry does not exist
    """
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
def patch_entry(entry_id: int):
    """Update entry content (author-only).

    Returns:
        200 with updated entry
        400 if content is missing/blank
        403 if current user is not the author
        404 if the entry does not exist
    """
    e = Entry.query.get_or_404(entry_id)

    # Author-only edit: keep this rule in one place for predictability.
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
def delete_entry(entry_id: int):
    """Delete an entry (author-only).

    Returns:
        204 on success (empty body)
        403 if current user is not the author
        404 if the entry does not exist
    """
    e = Entry.query.get_or_404(entry_id)

    # Author-only delete mirrors the patch rule for consistency.
    if e.user_id != session.get("user_id"):
        return _json_error("forbidden", 403)

    db.session.delete(e)
    db.session.commit()
    return "", 204

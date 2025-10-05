"""Pets API: create, list, read, update, and delete pets within a household.

All endpoints require a session (see @login_required_api). Responses use a minimal,
consistent JSON shape and standard HTTP status codes.
"""

from flask import Blueprint, request, session

from app.utils.auth import login_required_api

from ...models import Household, HouseholdMember, Pet, db
from .helpers import json_error as _json_error  # shared JSON error helper

pets_bp = Blueprint("pets", __name__, url_prefix="/api/v1")


def _is_member(household_id: int, user_id: int) -> bool:
    """Return True if the user belongs to the given household."""
    return (
        HouseholdMember.query.filter_by(
            household_id=household_id, user_id=user_id
        ).first()
        is not None
    )


def _pet_and_membership(pet_id: int, user_id: int):
    """Fetch a pet and whether the user is a member of its household.

    Returns:
        (None, None) if the pet doesn't exist.
        (Pet, bool) otherwise where bool indicates membership.
    """
    p = Pet.query.get(pet_id)
    if not p:
        return None, None
    is_mem = _is_member(p.household_id, user_id)
    return p, is_mem


@pets_bp.post("/households/<int:household_id>/pets")
@login_required_api
def create_pet(household_id: int):
    """Create a pet in a household (member-only).

    Request JSON:
        name: str (required)

    Returns:
        201 with {id, household_id, name} and Location header
        400 if name is missing/blank
        403 if user is not a member
        404 if household does not exist
    """
    Household.query.get_or_404(household_id)

    if not _is_member(household_id, session["user_id"]):
        return _json_error("forbidden", 403)

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return _json_error("name is required", 400)

    p = Pet(household_id=household_id, name=name)
    db.session.add(p)
    db.session.commit()

    body = {"id": p.id, "household_id": p.household_id, "name": p.name}
    return body, 201, {"Location": f"/api/v1/pets/{p.id}"}


@pets_bp.get("/households/<int:household_id>/pets")
@login_required_api
def list_pets(household_id: int):
    """List pets for a household (member-only), ordered by name.

    Returns:
        200 with a JSON array
        403 if user is not a member
        404 if household does not exist
    """
    Household.query.get_or_404(household_id)

    if not _is_member(household_id, session["user_id"]):
        return _json_error("forbidden", 403)

    pets = Pet.query.filter_by(household_id=household_id).order_by(Pet.name).all()
    return [
        {"id": p.id, "household_id": p.household_id, "name": p.name} for p in pets
    ], 200


@pets_bp.get("/pets/<int:pet_id>")
@login_required_api
def get_pet(pet_id: int):
    """Fetch a single pet (member-only).

    Returns:
        200 with pet JSON
        403 if user is not a member of the pet's household
        404 if pet does not exist
    """
    p, is_mem = _pet_and_membership(pet_id, session["user_id"])
    if p is None:
        return _json_error("not found", 404)
    if not is_mem:
        return _json_error("forbidden", 403)

    return {"id": p.id, "household_id": p.household_id, "name": p.name}, 200


@pets_bp.patch("/pets/<int:pet_id>")
@login_required_api
def patch_pet(pet_id: int):
    """Update a pet (member-only). Only 'name' is supported.

    Request JSON:
        name: str (optional; if present must be non-empty)

    Returns:
        200 with updated pet
        400 if provided name is empty
        403 if user is not a member
        404 if pet does not exist
    """
    p, is_mem = _pet_and_membership(pet_id, session["user_id"])
    if p is None:
        return _json_error("not found", 404)
    if not is_mem:
        return _json_error("forbidden", 403)

    data = request.get_json(silent=True) or {}
    if "name" in data:
        new_name = (data.get("name") or "").strip()
        if not new_name:
            return _json_error("name cannot be empty", 400)
        p.name = new_name

    db.session.commit()
    return {"id": p.id, "household_id": p.household_id, "name": p.name}, 200


@pets_bp.delete("/pets/<int:pet_id>")
@login_required_api
def delete_pet(pet_id: int):
    """Delete a pet (member-only).

    Returns:
        204 on success
        403 if user is not a member
        404 if pet does not exist
    """
    p, is_mem = _pet_and_membership(pet_id, session["user_id"])
    if p is None:
        return _json_error("not found", 404)
    if not is_mem:
        return _json_error("forbidden", 403)

    db.session.delete(p)
    db.session.commit()
    return "", 204

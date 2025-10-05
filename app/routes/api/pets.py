# app/routes/api/pets.py
# pet endpoints (JSON API)

from flask import Blueprint, request, session, jsonify
from ...models import db, Pet, Household, HouseholdMember
from app.utils.auth import login_required_api

pets_bp = Blueprint("pets", __name__, url_prefix="/api/v1")

def _json_error(msg, status):
    return jsonify(error=msg), status

def _is_member(household_id: int, user_id: int) -> bool:
    return HouseholdMember.query.filter_by(
        household_id=household_id, user_id=user_id
    ).first() is not None

def _pet_and_membership(pet_id: int, user_id: int):
    p = Pet.query.get(pet_id)
    if not p:
        return None, None
    is_mem = _is_member(p.household_id, user_id)
    return p, is_mem

@pets_bp.post("/households/<int:household_id>/pets")
@login_required_api
def create_pet(household_id):
    h = Household.query.get_or_404(household_id)

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
@login_required_api   # make GETs private to members; remove if you want them public
def list_pets(household_id):
    Household.query.get_or_404(household_id)

    if not _is_member(household_id, session["user_id"]):
        return _json_error("forbidden", 403)

    pets = Pet.query.filter_by(household_id=household_id).order_by(Pet.name).all()
    return [
        {"id": p.id, "household_id": p.household_id, "name": p.name}
        for p in pets
    ], 200

@pets_bp.get("/pets/<int:pet_id>")
@login_required_api
def get_pet(pet_id):
    p, is_mem = _pet_and_membership(pet_id, session["user_id"])
    if p is None:
        return _json_error("not found", 404)
    if not is_mem:
        return _json_error("forbidden", 403)

    return {"id": p.id, "household_id": p.household_id, "name": p.name}, 200

# PATCH instead of PUT for partial update
@pets_bp.patch("/pets/<int:pet_id>")
@login_required_api
def patch_pet(pet_id):
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
def delete_pet(pet_id):
    p, is_mem = _pet_and_membership(pet_id, session["user_id"])
    if p is None:
        return _json_error("not found", 404)
    if not is_mem:
        return _json_error("forbidden", 403)

    db.session.delete(p)
    db.session.commit()
    return "", 204
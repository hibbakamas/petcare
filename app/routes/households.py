# household endpoints

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from ..models import db, Household

households_bp = Blueprint("households", __name__, url_prefix="/api/v1/households")

@households_bp.post("")
def create_household():
    if not request.is_json:
        return {"error": "Content-Type must be application/json"}, 415
    data = request.get_json()
    name = data.get("name")
    join_code = data.get("join_code")

    if not name or not join_code:
        return {"error": "name and join_code required"}, 400

    h = Household(name=name, join_code=join_code)
    db.session.add(h)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "join_code already in use"}, 409

    body = {"id": h.id, "name": h.name, "join_code": h.join_code}
    return body, 201, {"Location": f"/api/v1/households/{h.id}"}

@households_bp.get("/<int:household_id>")
def get_household(household_id):
    h = Household.query.get_or_404(household_id)
    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 200

# PATCH instead of PUT for partial update
@households_bp.patch("/<int:household_id>")
def patch_household(household_id):
    h = Household.query.get_or_404(household_id)
    data = request.get_json() or {}
    if "name" not in data:
        return {"error": "name is required"}, 400
    h.name = data["name"]
    db.session.commit()
    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 200

@households_bp.delete("/<int:household_id>")
def delete_household(household_id):
    h = Household.query.get_or_404(household_id)
    db.session.delete(h)
    db.session.commit()
    return "", 204
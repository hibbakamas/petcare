# household endpoints

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from ..models import db, Household

households_bp = Blueprint("households", __name__, url_prefix="/api/v1/households")

@households_bp.post("")
def create_household():
    data = request.get_json(force=True)
    name = data.get("name")
    join_code = data.get("join_code")

    if not name or not join_code:
        return {"error": "name and join_code required"}, 400

    # create household
    h = Household(name=name, join_code=join_code)
    db.session.add(h)
    try:
        db.session.commit()
    except IntegrityError:
        # join code must be unique
        db.session.rollback()
        return {"error": "join_code already in use"}, 409

    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 201

@households_bp.get("/<int:household_id>")
def get_household(household_id):
    # look up household by id (404 if not found)
    h = Household.query.get_or_404(household_id)
    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 200

@households_bp.put("/<int:household_id>")
def update_household(household_id):
    # only name can be updated
    h = Household.query.get_or_404(household_id)
    data = request.get_json()

    new_name = data.get("name") if data else None
    if not new_name:
        return {"error": "name is required"}, 400

    h.name = new_name
    db.session.commit()

    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 200

@households_bp.delete("/<int:household_id>")
def delete_household(household_id):
    # delete household and any linked records
    h = Household.query.get_or_404(household_id)
    db.session.delete(h)
    db.session.commit()
    return {"deleted": True, "id": household_id}, 200
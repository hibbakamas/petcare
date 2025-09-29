# pet endpoints

from flask import Blueprint, request
from ..models import db, Pet, Household

pets_bp = Blueprint("pets", __name__, url_prefix="/api/v1")

@pets_bp.post("/households/<int:household_id>/pets")
def create_pet(household_id):
    Household.query.get_or_404(household_id)
    data = request.get_json()
    name = data.get("name")
    species = data.get("species")
    breed = data.get("breed")
    birthdate = data.get("birthdate")

    if not name:
        return {"error": "name is required"}, 400

    p = Pet(household_id=household_id, name=name, species=species, breed=breed)
    # parse birthday if given
    if birthdate:
        try:
            from datetime import date
            y, m, d = map(int, birthdate.split("-"))
            p.birthdate = date(y, m, d)
        except Exception:
            return {"error": "birthdate must be YYYY-MM-DD"}, 400

    db.session.add(p)
    db.session.commit()
    body = {
        "id": p.id,
        "household_id": p.household_id,
        "name": p.name,
        "species": p.species,
        "breed": p.breed,
        "birthdate": p.birthdate.isoformat() if p.birthdate else None,
    }
    return body, 201, {"Location": f"/api/v1/pets/{p.id}"}

@pets_bp.get("/households/<int:household_id>/pets")
def list_pets(household_id):
    Household.query.get_or_404(household_id)
    pets = Pet.query.filter_by(household_id=household_id).order_by(Pet.name).all()
    return [
        {
            "id": p.id,
            "household_id": p.household_id,
            "name": p.name,
            "species": p.species,
            "breed": p.breed,
            "birthdate": p.birthdate.isoformat() if p.birthdate else None,
        }
        for p in pets
    ], 200

@pets_bp.get("/pets/<int:pet_id>")
def get_pet(pet_id):
    p = Pet.query.get_or_404(pet_id)
    return {
        "id": p.id,
        "household_id": p.household_id,
        "name": p.name,
        "species": p.species,
        "breed": p.breed,
        "birthdate": p.birthdate.isoformat() if p.birthdate else None,
    }, 200

# PATCH instead of PUT for partial update
@pets_bp.patch("/pets/<int:pet_id>")
def patch_pet(pet_id):
    p = Pet.query.get_or_404(pet_id)
    data = request.get_json() or {}

    if "name" in data:
        if not data["name"]:
            return {"error": "name cannot be empty"}, 400
        p.name = data["name"]
    if "species" in data:
        p.species = data["species"]
    if "breed" in data:
        p.breed = data["breed"]
    if "birthdate" in data:
        bd = data["birthdate"]
        if bd:
            try:
                from datetime import date
                y, m, d = map(int, bd.split("-"))
                p.birthdate = date(y, m, d)
            except Exception:
                return {"error": "birthdate must be YYYY-MM-DD"}, 400
        else:
            p.birthdate = None

    db.session.commit()
    return {
        "id": p.id,
        "household_id": p.household_id,
        "name": p.name,
        "species": p.species,
        "breed": p.breed,
        "birthdate": p.birthdate.isoformat() if p.birthdate else None,
    }, 200

@pets_bp.delete("/pets/<int:pet_id>")
def delete_pet(pet_id):
    p = Pet.query.get_or_404(pet_id)
    db.session.delete(p)
    db.session.commit()
    return "", 204
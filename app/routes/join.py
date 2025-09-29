# join a household using join_code + nickname

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from ..models import db, Household, HouseholdMember, Users

join_bp = Blueprint("join", __name__, url_prefix="/api/v1")

@join_bp.post("/join")
def join_household():
    data = request.get_json()
    join_code = data.get("join_code")
    nickname  = data.get("nickname")
    username  = data.get("username")  # auth implemented later

    if not join_code or not nickname or not username:
        return {"error": "join_code, nickname, and username required"}, 400

    household = Household.query.filter_by(join_code=join_code).first()
    if not household:
        return {"error": "invalid join_code"}, 404
    
    user = Users.query.filter_by(username=username).first()
    if not user:
        return {"error": "user not found"}, 404
    
    created = False
    member = HouseholdMember.query.filter_by(user_id=user.id, household_id=household.id).first()
    if member:
        member.nickname = nickname
    else:
        member = HouseholdMember(user_id=user.id, household_id=household.id, nickname=nickname)
        db.session.add(member)
        created = True

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"error": "nickname already taken in this household"}, 409

    return {
        "household_id": household.id,
        "member_id": member.id,
        "household_name": household.name,
        "user": user.username,
        "nickname": member.nickname
    }, 201 if created else 200
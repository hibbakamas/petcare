# app/routes/api/households.py
# household endpoints (JSON API)

from flask import Blueprint, request, session, jsonify
from sqlalchemy.exc import IntegrityError
from ...models import db, Household, HouseholdMember, Users
from app.utils.auth import login_required_api  # decorator we added earlier
import random

households_bp = Blueprint("households", __name__, url_prefix="/api/v1/households")

def _json_error(msg, status):
    return jsonify(error=msg), status

def _gen_code(n=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))

def _require_membership(household_id: int):
    """Return (household, membership) or (None, None) if forbidden/not found."""
    h = Household.query.get(household_id)
    if not h:
        return None, None
    m = HouseholdMember.query.filter_by(
        user_id=session.get("user_id"), household_id=household_id
    ).first()
    if not m:
        return h, None
    return h, m

@households_bp.post("")
@login_required_api
def create_household():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    nickname = (data.get("nickname") or "").strip() or "Owner"

    if not name:
        return _json_error("name is required", 400)

    # generate unique join_code server-side
    code = _gen_code()
    while Household.query.filter_by(join_code=code).first():
        code = _gen_code()

    h = Household(name=name, join_code=code)
    db.session.add(h)
    db.session.commit()

    # add creator as a member
    m = HouseholdMember(user_id=session["user_id"], household_id=h.id, nickname=nickname)
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # very unlikely to collide, but fall back with suffix
        m = HouseholdMember(user_id=session["user_id"], household_id=h.id, nickname=f"{nickname} (owner)")
        db.session.add(m)
        db.session.commit()

    body = {"id": h.id, "name": h.name, "join_code": h.join_code}
    return body, 201, {"Location": f"/api/v1/households/{h.id}"}

@households_bp.get("/<int:household_id>")
@login_required_api
def get_household(household_id):
    h, m = _require_membership(household_id)
    if h is None:
        return _json_error("not found", 404)
    if m is None:
        return _json_error("forbidden", 403)
    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 200

# PATCH instead of PUT for partial update
@households_bp.patch("/<int:household_id>")
@login_required_api
def patch_household(household_id):
    h, m = _require_membership(household_id)
    if h is None:
        return _json_error("not found", 404)
    if m is None:
        return _json_error("forbidden", 403)

    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    if not new_name:
        return _json_error("name is required", 400)

    h.name = new_name
    db.session.commit()
    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 200

@households_bp.delete("/<int:household_id>")
@login_required_api
def delete_household(household_id):
    h, m = _require_membership(household_id)
    if h is None:
        return _json_error("not found", 404)
    if m is None:
        return _json_error("forbidden", 403)

    db.session.delete(h)
    db.session.commit()
    return "", 204

@households_bp.post("/join")  # POST /api/v1/households/join
@login_required_api
def join_household_api():
    data = request.get_json(silent=True) or {}

    # Accept either {"join_code": "..."} or {"code": "..."}
    join_code = (data.get("join_code") or data.get("code") or "").strip().upper()
    nickname  = (data.get("nickname") or "").strip() or "Member"

    if not join_code:
        return _json_error("join_code is required", 400)

    household = Household.query.filter_by(join_code=join_code).first()
    if not household:
        return _json_error("invalid join_code", 404)

    user_id = session["user_id"]  # guaranteed by @login_required_api
    user = Users.query.get(user_id)

    created = False
    member = HouseholdMember.query.filter_by(
        user_id=user_id, household_id=household.id
    ).first()

    if member:
        member.nickname = nickname  # update nickname if re-joining
    else:
        member = HouseholdMember(user_id=user_id, household_id=household.id, nickname=nickname)
        db.session.add(member)
        created = True

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _json_error("nickname already taken in this household", 409)

    return {
        "household_id": household.id,
        "household_name": household.name,
        "member_id": member.id,
        "user": user.username if user else None,
        "nickname": member.nickname,
    }, 201 if created else 200
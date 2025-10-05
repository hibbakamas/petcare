"""Households API: create, show, update, delete, and join.

All endpoints require a session (see @login_required_api). Responses use a minimal,
consistent JSON shape and standard HTTP status codes.
"""

import random

from flask import Blueprint, request, session
from sqlalchemy.exc import IntegrityError

from app.utils.auth import login_required_api

from ...models import Household, HouseholdMember, Users, db
from .helpers import json_error as _json_error  # shared JSON error helper

households_bp = Blueprint("households", __name__, url_prefix="/api/v1/households")


def _gen_code(n: int = 6) -> str:
    """Generate a readable join code (no ambiguous chars)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))


def _require_membership(household_id: int):
    """Return (household, membership) if the current user is a member.

    Returns:
        (None, None) if the household doesn't exist.
        (household, None) if the household exists but the user is not a member.
        (household, HouseholdMember) on success.
    """
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
    """Create a household and add the current user as a member.

    Request JSON:
        name: str (required)
        nickname: str (optional; defaults to "Owner")

    Returns:
        201 with {id, name, join_code} and Location header
        400 if name is missing/blank
    """
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    nickname = (data.get("nickname") or "").strip() or "Owner"

    if not name:
        return _json_error("name is required", 400)

    # Generate a unique join_code server-side.
    code = _gen_code()
    while Household.query.filter_by(join_code=code).first():
        code = _gen_code()

    h = Household(name=name, join_code=code)
    db.session.add(h)
    db.session.commit()

    # Add creator as a member. Nickname must be unique within a household.
    m = HouseholdMember(
        user_id=session["user_id"], household_id=h.id, nickname=nickname
    )
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Very unlikely nickname collision on first insert; append a suffix and retry.
        m = HouseholdMember(
            user_id=session["user_id"],
            household_id=h.id,
            nickname=f"{nickname} (owner)",
        )
        db.session.add(m)
        db.session.commit()

    body = {"id": h.id, "name": h.name, "join_code": h.join_code}
    return body, 201, {"Location": f"/api/v1/households/{h.id}"}


@households_bp.get("/<int:household_id>")
@login_required_api
def get_household(household_id: int):
    """Show a household if the current user is a member.

    Returns:
        200 with {id, name, join_code}
        403 if the user is not a member
        404 if the household doesn't exist
    """
    h, m = _require_membership(household_id)
    if h is None:
        return _json_error("not found", 404)
    if m is None:
        return _json_error("forbidden", 403)

    return {"id": h.id, "name": h.name, "join_code": h.join_code}, 200


@households_bp.patch("/<int:household_id>")
@login_required_api
def patch_household(household_id: int):
    """Rename a household (member required).

    Returns:
        200 with updated {id, name, join_code}
        400 if name is missing/blank
        403 if user is not a member
        404 if the household doesn't exist
    """
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
def delete_household(household_id: int):
    """Delete a household (member required).

    Returns:
        204 on success
        403 if user is not a member
        404 if the household doesn't exist
    """
    h, m = _require_membership(household_id)
    if h is None:
        return _json_error("not found", 404)
    if m is None:
        return _json_error("forbidden", 403)

    db.session.delete(h)
    db.session.commit()
    return "", 204


@households_bp.post("/join")
@login_required_api
def join_household_api():
    """Join a household by join_code, or update nickname if already a member.

    Request JSON:
        join_code or code: str (required)
        nickname: str (optional; defaults to "Member")

    Returns:
        201 with membership details if created
        200 with membership details if already a member (nickname updated)
        400 if join_code is missing
        404 if join_code is invalid
        409 if nickname already taken within this household
    """
    data = request.get_json(silent=True) or {}

    # Accept either {"join_code": "..."} or {"code": "..."}.
    join_code = (data.get("join_code") or data.get("code") or "").strip().upper()
    nickname = (data.get("nickname") or "").strip() or "Member"

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
        # Re-joins just update nickname.
        member.nickname = nickname
    else:
        member = HouseholdMember(
            user_id=user_id, household_id=household.id, nickname=nickname
        )
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
    }, (201 if created else 200)

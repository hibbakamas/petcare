"""Pytest fixtures and tiny factory helpers for the PetCare app."""

import os
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

# Ensure project root (containing "app/") is importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app  # noqa: E402
from app.models import Entry, Household, HouseholdMember, Pet, Users, db  # noqa: E402


@pytest.fixture(scope="function")
def app():
    """Create a fresh Flask app with an in-memory DB for each test."""
    flask_app = create_app(testing=True)
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with flask_app.app_context():
        db.create_all()
        try:
            yield flask_app
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    """Return a Flask test client bound to the fresh app."""
    return app.test_client()


# ----- tiny factory helpers -------------------------------------------------


@pytest.fixture
def make_user(app):
    def _make(username: str = "alice", password: str = "pw") -> Users:
        u = Users(username=username, password_hash=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        return u

    return _make


@pytest.fixture
def make_household(app):
    def _make(name: str = "Home", join_code: str = "ABC123") -> Household:
        h = Household(name=name, join_code=join_code)
        db.session.add(h)
        db.session.commit()
        return h

    return _make


@pytest.fixture
def add_member(app):
    def _add(user: Users, household: Household, nickname: str = "Owner") -> HouseholdMember:
        m = HouseholdMember(user_id=user.id, household_id=household.id, nickname=nickname)
        db.session.add(m)
        db.session.commit()
        return m

    return _add


@pytest.fixture
def make_pet(app):
    def _make(household: Household, name: str = "Pico") -> Pet:
        p = Pet(household_id=household.id, name=name)
        db.session.add(p)
        db.session.commit()
        return p

    return _make


@pytest.fixture
def make_entry(app):
    def _make(pet: Pet, user: Users, content: str = "Fed breakfast", created_at=None) -> Entry:
        e = Entry(pet_id=pet.id, user_id=user.id, content=content)
        if hasattr(e, "created_at") and created_at:
            e.created_at = created_at
        db.session.add(e)
        db.session.commit()
        return e

    return _make


# ----- session/login helpers ------------------------------------------------


@pytest.fixture
def login_ui(client, make_user):
    def _login(username: str = "alice", password: str = "pw"):
        make_user(username=username, password=password)
        resp = client.post("/login", data={"username": username, "password": password})
        assert resp.status_code in (302, 303)
        return resp

    return _login
# tests/conftest.py
import os
import sys
import pytest
from werkzeug.security import generate_password_hash

# Ensure project root (containing "app/") is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db, Users, Household, HouseholdMember, Pet, Entry


@pytest.fixture(scope="function")
def app():
    """Fresh app + in-memory DB per test (no cross-test leakage)."""
    flask_app = create_app(testing=True)  # <- uses TestingConfig (sqlite:///:memory:)
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    with flask_app.app_context():
        db.create_all()
        try:
            yield flask_app
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ---------- tiny factory helpers ----------

@pytest.fixture
def make_user(app):
    def _make(username="alice", password="pw"):
        u = Users(username=username, password_hash=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        return u
    return _make


@pytest.fixture
def make_household(app):
    def _make(name="Home", join_code="ABC123"):
        h = Household(name=name, join_code=join_code)
        db.session.add(h)
        db.session.commit()
        return h
    return _make


@pytest.fixture
def add_member(app):
    def _add(user, household, nickname="Owner"):
        m = HouseholdMember(user_id=user.id, household_id=household.id, nickname=nickname)
        db.session.add(m)
        db.session.commit()
        return m
    return _add


@pytest.fixture
def make_pet(app):
    def _make(household, name="Pico"):
        p = Pet(household_id=household.id, name=name)
        db.session.add(p)
        db.session.commit()
        return p
    return _make


@pytest.fixture
def make_entry(app):
    def _make(pet, user, content="Fed breakfast", created_at=None):
        e = Entry(pet_id=pet.id, user_id=user.id, content=content)
        if hasattr(e, "created_at") and created_at:
            e.created_at = created_at
        db.session.add(e)
        db.session.commit()
        return e
    return _make


# ---------- session helpers ----------

@pytest.fixture
def login_ui(client, make_user):
    def _login(username="alice", password="pw"):
        make_user(username=username, password=password)
        res = client.post("/login", data={"username": username, "password": password})
        assert res.status_code in (302, 303)
        return res
    return _login
# database models: household, user, pet, entry

from .db import db

class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    # users will join a household using this short code
    join_code = db.Column(db.String(6), unique=True, nullable=False)
    # when a household is deleted, also delete its pets and membership links
    pets = db.relationship(
        "Pet",
        backref="household",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    members = db.relationship(
        "HouseholdMember",
        backref="household",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # used for login
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    # deleting a user should delete only their membership links (not households)
    memberships = db.relationship(
        "HouseholdMember",
        backref="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # each pet belongs to exactly one household
    household_id = db.Column(db.Integer, db.ForeignKey('household.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String, nullable=False)
    # when a pet is deleted, also delete its entries
    entries = db.relationship(
        "Entry",
        backref="pet",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id', ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    # index to make entries for a pet ordered by time fast
    __table_args__ = (db.Index("ix_entries_pet_created", "pet_id", "created_at"),)

class HouseholdMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey('household.id', ondelete="CASCADE"), nullable=False)
    # displayed name
    nickname = db.Column(db.String, nullable=False)
    # same user can't join twice, same nickname can't be reused in same household
    __table_args__ = (db.UniqueConstraint("user_id", "household_id"), db.UniqueConstraint("household_id", "nickname"),)
"""Database models: Household, Users, Pet, Entry, HouseholdMember.

Relationships use cascading deletes so removing a parent cleans up dependents.
"""

from .db import db


class Household(db.Model):
    """A group that owns pets and has user memberships."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    # Users join via a short code; unique per household
    join_code = db.Column(db.String(6), unique=True, nullable=False)

    # When a household is deleted, also delete its pets and membership links
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
    """Application user."""

    id = db.Column(db.Integer, primary_key=True)
    # Used for login
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

    # Deleting a user removes only their membership links (not households)
    memberships = db.relationship(
        "HouseholdMember",
        backref="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Pet(db.Model):
    """A pet belonging to exactly one household."""

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(
        db.Integer,
        db.ForeignKey("household.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.String, nullable=False)

    # When a pet is deleted, also delete its entries
    entries = db.relationship(
        "Entry",
        backref="pet",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Entry(db.Model):
    """A note/log entry for a pet, authored by a user."""

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(
        db.Integer,
        db.ForeignKey("pet.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Index to make filtering/sorting entries-by-pet fast
    __table_args__ = (db.Index("ix_entries_pet_created", "pet_id", "created_at"),)


class HouseholdMember(db.Model):
    """Join table linking users to households with a per-household nickname."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    household_id = db.Column(
        db.Integer,
        db.ForeignKey("household.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Displayed name within the household
    nickname = db.Column(db.String, nullable=False)

    # Same user can't join twice; nicknames must be unique within a household
    __table_args__ = (
        db.UniqueConstraint("user_id", "household_id"),
        db.UniqueConstraint("household_id", "nickname"),
    )

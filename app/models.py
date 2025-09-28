# database models: household, user, pet, entry

from .db import db

class Household(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    # users will join a household using this short code
    join_code = db.Column(db.String(6), unique=True, nullable=False)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # used for login
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # each pet belongs to exactly one household
    household_id = db.Column(db.Integer, db.ForeignKey('household.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    # optional details
    species = db.Column(db.String)
    breed = db.Column(db.String)
    birthdate = db.Column(db.Date)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    # index to make entries for a pet ordered by time fast
    __table_args__ = (db.Index("ix_entries_pet_created", "pet_id", "created_at"),)

class HouseholdMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    household_id = db.Column(db.Integer, db.ForeignKey('household.id'), nullable=False)
    # displayed name
    nickname = db.Column(db.String, nullable=False)
    # same user can't join twice, same nickname can't be reused in same household
    __table_args__ = (db.UniqueConstraint("user_id", "household_id"), db.UniqueConstraint("household_id", "nickname"),)
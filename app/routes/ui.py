from flask import Blueprint, render_template, redirect, url_for, request, session
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import desc
from ..models import db, Users, Household, HouseholdMember, Pet, Entry
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

ui = Blueprint("ui", __name__)

# ------------------- Helpers -------------------
def _gen_code(n=6):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))

# ------------------- Home -------------------
@ui.get("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("ui.households_index"))
    return redirect(url_for("ui.login_get"))

# ------------------- Auth -------------------
@ui.get("/login")
def login_get():
    return render_template("login.html")

@ui.post("/login")
def login_post():
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    if not username or not password:
        return render_template("login.html", error="Please fill in both fields."), 400

    user = db.session.query(Users).filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render_template("login.html", error="Invalid username or password."), 401

    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("ui.households_index"))

@ui.get("/signup")
def signup_get():
    return render_template("signup.html")

@ui.post("/signup")
def signup_post():
    username = (request.form.get("username") or "").strip()
    password = (request.form.get("password") or "").strip()
    if not username or not password:
        return render_template("signup.html", error="Please fill in both fields."), 400

    if db.session.query(Users).filter_by(username=username).first():
        return render_template("signup.html", error="That username is taken."), 409

    user = Users(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username
    return redirect(url_for("ui.households_index"))

@ui.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("ui.login_get"))

# ------------------- Households Hub -------------------
@ui.get("/households")
def households_index():
    user_id = session.get("user_id")
    memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
    return render_template("households_index.html", memberships=memberships)

# ------------------- Create Household -------------------
@ui.get("/households/new")
def households_new_get():
    return render_template("households_new.html")

@ui.post("/households/new")
def households_new_post():
    name = request.form.get("name", "").strip()
    nickname = (request.form.get("nickname", "") or session.get("username", "") or "Owner").strip()

    if not name:
        return render_template("households_new.html", error="Household name is required.")

    # unique join code
    code = _gen_code()
    while db.session.query(Household).filter_by(join_code=code).first():
        code = _gen_code()

    # create household
    h = Household(name=name, join_code=code)
    db.session.add(h)
    db.session.commit()

    # add creator as member with chosen nickname
    m = HouseholdMember(user_id=session["user_id"], household_id=h.id, nickname=nickname or "Owner")
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Extremely unlikely to collide on a fresh household, but just in case:
        m = HouseholdMember(user_id=session["user_id"], household_id=h.id, nickname=f"{nickname or 'Owner'} (owner)")
        db.session.add(m)
        db.session.commit()

    return redirect(url_for("ui.household_dashboard", household_id=h.id))

# ------------------- Join Household -------------------
@ui.get("/join")
def join_get():
    return render_template("join.html")

@ui.post("/join")
def join_post():
    code = request.form.get("code", "").strip().upper()
    nickname = (request.form.get("nickname", "") or session.get("username", "") or "").strip()

    if not code:
        return render_template("join.html", error="Join code is required.")

    h = db.session.query(Household).filter_by(join_code=code).first()
    if not h:
        return render_template("join.html", error="Invalid join code. Please try again.")

    # Already a member? -> block and offer to open it
    existing = db.session.query(HouseholdMember).filter_by(
        user_id=session["user_id"], household_id=h.id
    ).first()
    if existing:
        return render_template(
            "join.html",
            error="You’re already a member of this household.",
            existing_household=h
        )

    # New membership
    if not nickname:
        nickname = session.get("username", "Member")

    m = HouseholdMember(user_id=session["user_id"], household_id=h.id, nickname=nickname)
    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return render_template("join.html", error="Nickname already in use in this household. Try another.")

    return redirect(url_for("ui.household_dashboard", household_id=h.id))

@ui.post("/households/<int:household_id>/leave")
def households_leave(household_id):
    m = db.session.query(HouseholdMember).filter_by(
        user_id=session["user_id"], household_id=household_id
    ).first()
    if not m:
        return render_template("errors/404.html"), 404
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("ui.households_index"))


# ------------------- Household Dashboard -------------------
@ui.get("/households/<int:household_id>")
def household_dashboard(household_id):
    h = db.session.get(Household, household_id)
    if not h:
        return render_template("errors/404.html"), 404
    pets = h.pets
    members = h.members
    return render_template("households_show.html", household=h, pets=pets, members=members)

# ------------------- Pets -------------------
@ui.get("/households/<int:household_id>/pets/new")
def pets_new_get(household_id):
    return render_template("pets_new.html", household_id=household_id)

@ui.post("/households/<int:household_id>/pets/new")
def pets_new_post(household_id):
    name = request.form.get("name", "").strip()
    if not name:
        return render_template("pets_new.html", household_id=household_id, error="Pet name is required.")
    p = Pet(household_id=household_id, name=name)
    db.session.add(p)
    db.session.commit()
    return redirect(url_for("ui.household_dashboard", household_id=household_id))

@ui.post("/households/<int:household_id>/pets/<int:pet_id>/delete")
def pets_delete(household_id, pet_id):
    p = db.session.get(Pet, pet_id)
    if not p or p.household_id != household_id:
        return render_template("errors/404.html"), 404
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("ui.household_dashboard", household_id=household_id))

# ---- Pet detail ----
@ui.get("/pets/<int:pet_id>")
def pets_show(pet_id):
    pet = db.session.get(Pet, pet_id)
    if not pet:
        return render_template("errors/404.html"), 404

    # range filter: day (default) | week | month | all
    rng = (request.args.get("range") or "day").lower()
    now = datetime.utcnow()
    if rng == "week":
        start = now - timedelta(days=7)
    elif rng == "month":
        start = now - timedelta(days=30)
    elif rng == "all":
        start = None
    else:  # "day"
        start = now - timedelta(days=1)

    q = db.session.query(Entry).filter(Entry.pet_id == pet_id)
    if start:
        q = q.filter(Entry.created_at >= start)
    entries = q.order_by(desc(Entry.created_at)).all()

    # 👇 nickname map from this pet's household: user_id -> nickname
    members_map = {m.user_id: m.nickname for m in pet.household.members}

    return render_template(
        "pets_show.html",
        pet=pet,
        entries=entries,
        range=rng,
        members_map=members_map
    )

# ---- Add entry ----
@ui.post("/pets/<int:pet_id>/entries/new")
def entries_create(pet_id):
    pet = db.session.get(Pet, pet_id)
    if not pet:
        return render_template("errors/404.html"), 404

    content = (request.form.get("content") or "").strip()
    if not content:
        # re-render with error
        return render_template(
            "pets_show.html",
            pet=pet,
            entries=db.session.query(Entry).filter_by(pet_id=pet_id).order_by(desc(Entry.created_at)).all(),
            range="day",
            error="Entry text is required."
        )

    e = Entry(pet_id=pet_id, user_id=session["user_id"], content=content)
    db.session.add(e)
    db.session.commit()
    return redirect(url_for("ui.pets_show", pet_id=pet_id))

# ---- Delete entry ----
@ui.post("/pets/<int:pet_id>/entries/<int:entry_id>/delete")
def entries_delete(pet_id, entry_id):
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    # Only the author can delete
    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    db.session.delete(e)
    db.session.commit()
    return redirect(url_for("ui.pets_show", pet_id=pet_id))


# ---- Edit entry (GET shows form) ----
@ui.get("/pets/<int:pet_id>/entries/<int:entry_id>/edit")
def entries_edit_get(pet_id, entry_id):
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    # Only the author can edit
    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    return render_template("entries_edit.html", pet_id=pet_id, entry=e)


# ---- Edit entry (POST updates) ----
@ui.post("/pets/<int:pet_id>/entries/<int:entry_id>/edit")
def entries_edit_post(pet_id, entry_id):
    e = db.session.get(Entry, entry_id)
    if not e or e.pet_id != pet_id:
        return render_template("errors/404.html"), 404

    # Only the author can edit
    if e.user_id != session.get("user_id"):
        return render_template("errors/403.html"), 403

    content = (request.form.get("content") or "").strip()
    if not content:
        return render_template("entries_edit.html", pet_id=pet_id, entry=e,
                               error="Content cannot be empty.")

    e.content = content
    db.session.commit()
    return redirect(url_for("ui.pets_show", pet_id=pet_id))

# -------- Profile (view) --------
@ui.get("/profile")
def profile_get():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("ui.login_get"))

    user = db.session.get(Users, user_id)
    # memberships for this user -> show household name + editable nickname
    memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
    return render_template("profile.html", user=user, memberships=memberships)


# -------- Update username --------
@ui.post("/profile/username")
def profile_update_username():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("ui.login_get"))

    new_username = (request.form.get("username") or "").strip()
    if not new_username:
        # re-render with error
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               username_error="Username cannot be empty.")

    # enforce uniqueness
    if db.session.query(Users).filter(Users.username == new_username, Users.id != user_id).first():
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               username_error="That username is already taken.")

    user = db.session.get(Users, user_id)
    user.username = new_username
    db.session.commit()

    # keep session in sync
    session["username"] = new_username
    return redirect(url_for("ui.profile_get"))


# -------- Update my nickname in a household --------
@ui.post("/households/<int:household_id>/nickname")
def profile_update_nickname(household_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("ui.login_get"))

    new_nick = (request.form.get("nickname") or "").strip()
    if not new_nick:
        # re-render profile with an error specific to this household
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               nickname_errors={household_id: "Nickname cannot be empty."})

    m = db.session.query(HouseholdMember).filter_by(user_id=user_id, household_id=household_id).first()
    if not m:
        # not your membership
        return redirect(url_for("ui.profile_get"))

    m.nickname = new_nick
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        user = db.session.get(Users, user_id)
        memberships = db.session.query(HouseholdMember).filter_by(user_id=user_id).all()
        return render_template("profile.html", user=user, memberships=memberships,
                               nickname_errors={household_id: "That nickname is already used in this household."})

    return redirect(url_for("ui.profile_get"))



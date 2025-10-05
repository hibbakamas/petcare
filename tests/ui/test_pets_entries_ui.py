# tests/ui/test_pets_entries_ui.py
from datetime import datetime, timedelta

def setup_household_pet(client, login_ui, make_household, add_member, make_pet):
    """helper to create: user (via login), household, membership, pet -> return (user, household, pet)"""
    login_ui("petter", "pw")
    from app.models import Users
    user = Users.query.filter_by(username="petter").first()
    h = make_household(name="Zoo", join_code="ZOO123")
    add_member(user, h, nickname="Zookeeper")
    p = make_pet(h, name="Mochi")
    return user, h, p

def test_pet_page_and_add_entry(client, login_ui, make_household, add_member, make_pet):
    user, h, p = setup_household_pet(client, login_ui, make_household, add_member, make_pet)
    # view pet page
    r = client.get(f"/pets/{p.id}")
    assert r.status_code == 200
    assert b"Mochi" in r.data

    # add entry
    r = client.post(f"/pets/{p.id}/entries/new", data={"content": "Went for a walk"}, follow_redirects=False)
    assert r.status_code == 302
    assert f"/pets/{p.id}" in r.headers["Location"]

    # page now shows entry
    r2 = client.get(f"/pets/{p.id}", follow_redirects=True)
    assert b"Went for a walk" in r2.data

def test_edit_delete_entry_permissions(client, login_ui, make_household, add_member, make_pet, make_entry):
    # author user
    login_ui("author", "pw")
    from app.models import Users
    author = Users.query.filter_by(username="author").first()
    h = make_household(name="HH", join_code="HH1234")
    add_member(author, h, nickname="A")
    p = make_pet(h, name="Taro")
    e = make_entry(p, author, "Original")

    # author can edit GET
    r = client.get(f"/pets/{p.id}/entries/{e.id}/edit")
    assert r.status_code == 200
    assert b"Original" in r.data

    # author can edit POST
    r = client.post(f"/pets/{p.id}/entries/{e.id}/edit", data={"content": "Updated"}, follow_redirects=False)
    assert r.status_code == 302

    # author can delete
    r = client.post(f"/pets/{p.id}/entries/{e.id}/delete", follow_redirects=False)
    assert r.status_code == 302

def test_other_user_cannot_edit_or_delete(client, login_ui, make_household, add_member, make_pet, make_entry):
    # create entry by alice
    login_ui("alice", "pw")
    from app.models import Users
    alice = Users.query.filter_by(username="alice").first()
    h = make_household(name="HH2", join_code="HH2ABC")
    add_member(alice, h, nickname="A")
    p = make_pet(h, name="Bean")
    e = make_entry(p, alice, "Mine")

    # logout and login as bob
    client.get("/logout")
    login_ui("bob", "pw")

    # bob should get 403 on edit & delete
    r1 = client.get(f"/pets/{p.id}/entries/{e.id}/edit")
    assert r1.status_code == 403
    r2 = client.post(f"/pets/{p.id}/entries/{e.id}/edit", data={"content": "Nope"})
    assert r2.status_code == 403
    r3 = client.post(f"/pets/{p.id}/entries/{e.id}/delete")
    assert r3.status_code == 403

def test_add_pet_validation_and_delete(client, login_ui):
    login_ui("petuser", "pw")
    client.post("/households/new", data={"name":"HPets","nickname":"O"})
    # validate empty name
    r = client.post("/households/1/pets/new", data={"name": ""})
    assert r.status_code == 200
    assert b"Pet name is required" in r.data

    # add valid pet
    r = client.post("/households/1/pets/new", data={"name": "Bean"})
    assert r.status_code in (302, 303)

    # show pet detail with range filters
    for rng in ("today","week","month","all"):
        rr = client.get(f"/pets/1?range={rng}")
        assert rr.status_code == 200

    # delete pet
    r = client.post("/households/1/pets/1/delete")
    assert r.status_code in (302, 303)

def test_entry_create_validation(client, login_ui):
    login_ui("entryuser", "pw")
    client.post("/households/new", data={"name":"HEntries","nickname":"O"})
    client.post("/households/1/pets/new", data={"name": "Milo"})
    # empty content returns page with error
    r = client.post("/pets/1/entries/new", data={"content": ""})
    assert r.status_code == 200
    assert b"Entry text is required" in r.data

    # valid entry
    r = client.post("/pets/1/entries/new", data={"content": "Fed breakfast"})
    assert r.status_code in (302, 303)
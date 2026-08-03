import pytest

from firstsite.models import Note


@pytest.mark.django_db
def test_toggle_pin_plain_post_still_redirects(auth_client, note):
    """No-JS fallback: a plain POST (no HX-Request header) behaves as before."""
    r = auth_client.post(f"/notes/{note.pk}/toggle-pin/")
    assert r.status_code == 302
    note.refresh_from_db()
    assert note.is_pinned is True


@pytest.mark.django_db
def test_toggle_pin_htmx_request_returns_card_fragment(auth_client, note):
    r = auth_client.post(f"/notes/{note.pk}/toggle-pin/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    note.refresh_from_db()
    assert note.is_pinned is True
    assert f'id="note-card-{note.pk}"'.encode() in r.content
    assert b"Pinned" in r.content
    assert b"Unpin" in r.content
    # A fragment response, not a full page.
    assert b"<html" not in r.content


@pytest.mark.django_db
def test_toggle_archive_htmx_request_returns_card_fragment(auth_client, note):
    r = auth_client.post(f"/notes/{note.pk}/toggle-archive/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    note.refresh_from_db()
    assert note.is_archived is True
    assert f'id="note-card-{note.pk}"'.encode() in r.content
    assert b"Archived" in r.content
    assert b"Restore" in r.content


@pytest.mark.django_db
def test_toggle_pin_htmx_rejects_other_users_note(client, note):
    from django.contrib.auth.models import User
    other = User.objects.create_user(username="eve", password="pass1234")
    client.login(username="eve", password="pass1234")
    r = client.post(f"/notes/{note.pk}/toggle-pin/", HTTP_HX_REQUEST="true")
    assert r.status_code == 404
    note.refresh_from_db()
    assert note.is_pinned is False


@pytest.mark.django_db
def test_note_list_renders_htmx_attributes_on_pin_archive_forms(auth_client, note):
    r = auth_client.get("/notes/list/")
    assert r.status_code == 200
    assert f'hx-target="#note-card-{note.pk}"'.encode() in r.content
    assert b'hx-swap="outerHTML"' in r.content

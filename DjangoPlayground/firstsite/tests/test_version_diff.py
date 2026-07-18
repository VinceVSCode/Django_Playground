import pytest
from firstsite.models import Note, NoteVersion


@pytest.mark.django_db
def test_version_diff_requires_login(client, user):
    note = Note.objects.create(owner=user, title="T", content="hello")
    version = NoteVersion.objects.create(note=note, title="T", content="hello", updated_by=user)
    r = client.get(f"/notes/{note.pk}/versions/{version.pk}/diff/")
    assert r.status_code == 302
    assert "/accounts/login/" in r.headers["Location"]


@pytest.mark.django_db
def test_version_diff_shows_added_and_removed_lines(auth_client, user):
    # Version snapshot = old text; current note = new text
    note = Note.objects.create(owner=user, title="Title v2", content="line one\nline two")
    version = NoteVersion.objects.create(
        note=note, title="Title v1", content="line one\nOLD line", updated_by=user
    )
    r = auth_client.get(f"/notes/{note.pk}/versions/{version.pk}/diff/")
    assert r.status_code == 200
    body = r.content.decode()
    # Removed line (from the old version) and added line (in the current note) both shown
    assert "OLD line" in body        # removed
    assert "line two" in body        # added
    assert "diff-del" in body and "diff-add" in body
    # Title change is rendered too
    assert "Title v1" in body and "Title v2" in body


@pytest.mark.django_db
def test_version_diff_rejects_other_users_note(auth_client, django_user_model):
    # A note owned by someone else must not be diffable
    other = django_user_model.objects.create_user(username="mallory", password="x")
    note = Note.objects.create(owner=other, title="secret", content="secret")
    version = NoteVersion.objects.create(note=note, title="secret", content="secret", updated_by=other)
    r = auth_client.get(f"/notes/{note.pk}/versions/{version.pk}/diff/")
    assert r.status_code == 404

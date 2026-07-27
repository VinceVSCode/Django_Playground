import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from firstsite.models import Note, NoteShare


@pytest.fixture
def viewer(db):
    return User.objects.create_user(username="bob", password="pass1234")


@pytest.fixture
def viewer_client(client, viewer):
    client.login(username="bob", password="pass1234")
    return client


@pytest.mark.django_db
def test_noteshare_unique_together(user, viewer, note):
    NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    with pytest.raises(IntegrityError):
        NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)


@pytest.mark.django_db
def test_share_flow_creates_noteshare(auth_client, user, viewer, note):
    r1 = auth_client.get(f"/notes/{note.pk}/share/")
    assert r1.status_code == 200

    r2 = auth_client.post(f"/notes/{note.pk}/share/", data={"recipient_username": viewer.username})
    assert r2.status_code in (302, 303)
    assert NoteShare.objects.filter(note=note, shared_with=viewer, shared_by=user).exists()

    # Note is NOT copied (unlike Send) — still only one Note row.
    assert Note.objects.filter(title=note.title).count() == 1


@pytest.mark.django_db
def test_cannot_share_with_self(auth_client, note, user):
    r = auth_client.post(f"/notes/{note.pk}/share/", data={"recipient_username": user.username})
    assert r.status_code == 200  # form re-rendered with error
    assert not NoteShare.objects.filter(note=note, shared_with=user).exists()


@pytest.mark.django_db
def test_sharing_twice_is_idempotent(auth_client, user, viewer, note):
    NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    r = auth_client.post(f"/notes/{note.pk}/share/", data={"recipient_username": viewer.username})
    assert r.status_code in (302, 303)
    assert NoteShare.objects.filter(note=note, shared_with=viewer).count() == 1


@pytest.mark.django_db
def test_shared_viewer_can_view_note_readonly(viewer_client, user, viewer, note):
    NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    r = viewer_client.get(f"/notes/{note.pk}/")
    assert r.status_code == 200
    assert b"Read-only" in r.content
    # No edit/delete/share links for a non-owner viewer
    assert f'/notes/{note.pk}/edit/'.encode() not in r.content
    assert f'/notes/{note.pk}/delete/'.encode() not in r.content


@pytest.mark.django_db
def test_non_shared_user_gets_404(viewer_client, note):
    r = viewer_client.get(f"/notes/{note.pk}/")
    assert r.status_code == 404


@pytest.mark.django_db
def test_viewer_cannot_edit_or_delete_shared_note(viewer_client, user, viewer, note):
    NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    r_edit = viewer_client.post(f"/notes/{note.pk}/edit/", data={"title": "Hacked", "content": "x"})
    assert r_edit.status_code == 404
    r_delete = viewer_client.post(f"/notes/{note.pk}/delete/")
    assert r_delete.status_code == 404
    note.refresh_from_db()
    assert note.title != "Hacked"
    assert not note.is_trashed


@pytest.mark.django_db
def test_only_owner_can_share_or_unshare(viewer_client, user, viewer, note):
    r_share = viewer_client.get(f"/notes/{note.pk}/share/")
    assert r_share.status_code == 404

    share = NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    r_unshare = viewer_client.post(f"/notes/{note.pk}/share/{share.pk}/unshare/")
    assert r_unshare.status_code == 404
    assert NoteShare.objects.filter(pk=share.pk).exists()


@pytest.mark.django_db
def test_owner_can_unshare(auth_client, user, viewer, note):
    share = NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    r = auth_client.post(f"/notes/{note.pk}/share/{share.pk}/unshare/")
    assert r.status_code in (302, 303)
    assert not NoteShare.objects.filter(pk=share.pk).exists()


@pytest.mark.django_db
def test_recipient_can_leave_share(viewer_client, user, viewer, note):
    share = NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    r = viewer_client.post(f"/notes/{note.pk}/leave-share/")
    assert r.status_code in (302, 303)
    assert not NoteShare.objects.filter(pk=share.pk).exists()


@pytest.mark.django_db
def test_shared_with_me_list(viewer_client, user, viewer, note):
    NoteShare.objects.create(note=note, shared_by=user, shared_with=viewer)
    r = viewer_client.get("/shared-with-me/")
    assert r.status_code == 200
    assert note.title.encode() in r.content

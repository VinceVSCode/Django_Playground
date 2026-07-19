import pytest
from django.utils import timezone
from firstsite.models import Note, NoteEvent


@pytest.mark.django_db
def test_delete_moves_note_to_trash(auth_client, user):
    note = Note.objects.create(owner=user, title="Doomed", content="x")
    r = auth_client.post(f"/notes/{note.pk}/delete/")
    assert r.status_code == 302

    # Row still exists, but is soft-deleted
    note.refresh_from_db()
    assert note.deleted_at is not None
    # Default manager hides it; all_objects still sees it
    assert not Note.objects.filter(pk=note.pk).exists()
    assert Note.all_objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_trashed_note_hidden_from_list_and_detail(auth_client, user):
    note = Note.objects.create(owner=user, title="Hidden", content="x")
    auth_client.post(f"/notes/{note.pk}/delete/")

    # Not in the notes list
    list_body = auth_client.get("/notes/list/").content.decode()
    assert "Hidden" not in list_body
    # Detail 404s
    assert auth_client.get(f"/notes/{note.pk}/").status_code == 404
    # But it shows up in the Trash
    trash_body = auth_client.get("/trash/").content.decode()
    assert "Hidden" in trash_body


@pytest.mark.django_db
def test_restore_brings_note_back(auth_client, user):
    note = Note.objects.create(owner=user, title="Comeback", content="x")
    auth_client.post(f"/notes/{note.pk}/delete/")
    r = auth_client.post(f"/notes/{note.pk}/restore/")
    assert r.status_code == 302

    note.refresh_from_db()
    assert note.deleted_at is None
    assert Note.objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_purge_permanently_deletes(auth_client, user):
    note = Note.objects.create(owner=user, title="Gone", content="x")
    auth_client.post(f"/notes/{note.pk}/delete/")
    r = auth_client.post(f"/notes/{note.pk}/purge/")
    assert r.status_code == 302
    assert not Note.all_objects.filter(pk=note.pk).exists()


@pytest.mark.django_db
def test_empty_trash_purges_only_trashed(auth_client, user):
    keep = Note.objects.create(owner=user, title="Keep", content="x")
    a = Note.objects.create(owner=user, title="A", content="x")
    b = Note.objects.create(owner=user, title="B", content="x")
    auth_client.post(f"/notes/{a.pk}/delete/")
    auth_client.post(f"/notes/{b.pk}/delete/")

    r = auth_client.post("/trash/empty/")
    assert r.status_code == 302
    assert not Note.all_objects.filter(pk__in=[a.pk, b.pk]).exists()
    assert Note.objects.filter(pk=keep.pk).exists()


# --- analytics: soft-delete behaves like the old hard delete ---

@pytest.mark.django_db
def test_soft_delete_logs_single_delete_event(auth_client, user):
    note = Note.objects.create(owner=user, title="Audited", content="x")
    # creating the note logged a 'create'; clear counts by measuring deltas
    updates_before = NoteEvent.objects.filter(user=user, action="update").count()

    auth_client.post(f"/notes/{note.pk}/delete/")

    assert NoteEvent.objects.filter(user=user, note=note, action="delete").count() == 1
    # soft-delete must NOT masquerade as an 'update'
    assert NoteEvent.objects.filter(user=user, action="update").count() == updates_before


@pytest.mark.django_db
def test_purge_and_restore_log_no_extra_events(auth_client, user):
    note = Note.objects.create(owner=user, title="Quiet", content="x")
    auth_client.post(f"/notes/{note.pk}/delete/")          # 1 delete event
    auth_client.post(f"/notes/{note.pk}/restore/")         # no event
    auth_client.post(f"/notes/{note.pk}/delete/")          # 1 more delete event
    auth_client.post(f"/notes/{note.pk}/purge/")           # no event

    assert NoteEvent.objects.filter(user=user, action="delete").count() == 2
    assert NoteEvent.objects.filter(user=user, action="update").count() == 0


# --- ownership isolation ---

@pytest.mark.django_db
def test_cannot_trash_or_restore_other_users_note(auth_client, django_user_model):
    other = django_user_model.objects.create_user(username="mallory", password="x")
    note = Note.objects.create(owner=other, title="Secret", content="x")

    assert auth_client.post(f"/notes/{note.pk}/delete/").status_code == 404
    # even if it were trashed, restore/purge must 404 for a non-owner
    note.deleted_at = timezone.now()
    note.save(update_fields=["deleted_at"])
    assert auth_client.post(f"/notes/{note.pk}/restore/").status_code == 404
    assert auth_client.post(f"/notes/{note.pk}/purge/").status_code == 404

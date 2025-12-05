import pytest
from django.contrib.auth.models import User
from firstsite.models import Note, NoteSend, NoteEvent

@pytest.mark.django_db
def test_api_send_creates_copy_and_logs(client, user):
    recipient = User.objects.create_user("bob", password="x")
    note = Note.objects.create(title="T", content="C", owner=user)

    client.defaults['HTTP_AUTHORIZATION'] = f"Token {user.auth_token.key}"
    r = client.post(f"/api/notes/{note.pk}/send/", data={"recipient_username": "bob"}, content_type="application/json")
    assert r.status_code == 201

    # copy exists
    assert Note.objects.filter(owner=recipient, title="T").count() == 1
    # domain log
    assert NoteSend.objects.filter(sender=user, recipient=recipient, original_note=note).exists()
    # analytics events
    assert NoteEvent.objects.filter(user=user, action="send").exists()
    assert NoteEvent.objects.filter(user=user, action="create").exists()  # the copy creation via signal

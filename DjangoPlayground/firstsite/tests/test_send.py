import json
import pytest
from django.contrib.auth.models import User
from firstsite.models import Note, NoteSend, NoteEvent
from rest_framework.authtoken.models import Token

# Helper to get auth header for a user
def auth_header(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {"HTTP_AUTHORIZATION": f"Token {token.key}"}

@pytest.mark.django_db
def test_send_note_html_flow(client,user):
    # create recipient user
    recipient = User.objects.create_user(username="testing_user", password="pass1234")
    # create a note to send
    note = Note.objects.create(owner=user, title="Test Note", content="Hello Test.")

    # GET form
    r1 = client.get(f"/notes/{note.pk}/send/")
    assert r1.status_code == 200

    #POST form
    r2 = client.post(f"/notes/{note.pk}/send/", data={"recipient_username": recipient.username})
    assert r2.status_code in (302, 303)  # redirect back to detail

    #Recipient got a copy
    assert Note.objects.filter(owner=recipient, title="Test Note", content="Hello Test.").exists()

    # NoteSend logged
    assert NoteSend.objects.filter(sender=user, recipient=recipient, original_note=note).exists()

    # NoteEvent('send') logged for sender
    assert NoteEvent.objects.filter(user=user, note__original_note=note, action=NoteEvent.ACTION_SEND).exists()

@pytest.mark.django_db
def test_send_note_api_happy_path(client, user):
    """
    Test sending a note via the API (happy path).
    """
    note = Note.objects.create(title="X", content="Y", owner=user)
    r = client.post(
        f"/api/notes/{note.pk}/send/",
        data=json.dumps({"recipient_username": "nobody"}),
        content_type="application/json",
        **auth_header(user)
    )

    assert r.status_code == 404 # No such user



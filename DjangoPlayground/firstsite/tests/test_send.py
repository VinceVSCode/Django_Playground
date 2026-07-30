import json
import pytest
from django.contrib.auth.models import User
from firstsite.models import Note, NoteSend, NoteEvent, Tag
from rest_framework.authtoken.models import Token

# Helper to get auth header for a user
def auth_header(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {"HTTP_AUTHORIZATION": f"Token {token.key}"}

@pytest.mark.django_db
def test_send_note_html_flow(auth_client, user):
    # auth_client is logged in as `user` (see conftest.py)
    # create recipient user
    recipient = User.objects.create_user(username="testing_user", password="pass1234")
    # create a note to send
    note = Note.objects.create(owner=user, title="Test Note", content="Hello Test.")

    # GET form
    r1 = auth_client.get(f"/notes/{note.pk}/send/")
    assert r1.status_code == 200

    #POST form
    r2 = auth_client.post(f"/notes/{note.pk}/send/", data={"recipient_username": recipient.username})
    assert r2.status_code in (302, 303)  # redirect back to detail

    #Recipient got a copy
    assert Note.objects.filter(owner=recipient, title="Test Note", content="Hello Test.").exists()

    # NoteSend logged
    assert NoteSend.objects.filter(sender=user, recipient=recipient, original_note=note).exists()

    # NoteEvent('send') logged for sender (event.note is the original note)
    assert NoteEvent.objects.filter(user=user, note=note, action=NoteEvent.ACTION_SEND).exists()

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


@pytest.mark.django_db
def test_send_note_html_copies_tags_by_name_not_sender_rows(auth_client, user):
    """T-08: recipient gets their own Tag row (by name), not the sender's."""
    recipient = User.objects.create_user(username="testing_user2", password="pass1234")
    sender_tag = Tag.objects.create(owner=user, name="Work")
    note = Note.objects.create(owner=user, title="Tagged Note", content="Body")
    note.tags.set([sender_tag])

    r = auth_client.post(f"/notes/{note.pk}/send/", data={"recipient_username": recipient.username})
    assert r.status_code in (302, 303)

    copy = Note.objects.get(owner=recipient, title="Tagged Note")
    copy_tags = list(copy.tags.all())
    assert len(copy_tags) == 1
    assert copy_tags[0].name == "Work"
    assert copy_tags[0].owner == recipient
    assert copy_tags[0].pk != sender_tag.pk

    # Recipient can see/manage it as their own tag.
    assert Tag.objects.filter(owner=recipient, name="Work").exists()


@pytest.mark.django_db
def test_send_note_reuses_recipients_existing_tag_of_same_name(auth_client, user):
    """Sending twice (or to a recipient who already has that tag name) doesn't duplicate it."""
    recipient = User.objects.create_user(username="testing_user3", password="pass1234")
    recipient_tag = Tag.objects.create(owner=recipient, name="Work")
    sender_tag = Tag.objects.create(owner=user, name="Work")
    note = Note.objects.create(owner=user, title="Another Note", content="Body")
    note.tags.set([sender_tag])

    r = auth_client.post(f"/notes/{note.pk}/send/", data={"recipient_username": recipient.username})
    assert r.status_code in (302, 303)

    assert Tag.objects.filter(owner=recipient, name="Work").count() == 1
    copy = Note.objects.get(owner=recipient, title="Another Note")
    assert list(copy.tags.all()) == [recipient_tag]


@pytest.mark.django_db
def test_send_note_api_copies_tags_by_name(user):
    recipient = User.objects.create_user(username="testing_user4", password="pass1234")
    sender_tag = Tag.objects.create(owner=user, name="Ideas")
    note = Note.objects.create(owner=user, title="API Tagged Note", content="Body")
    note.tags.set([sender_tag])

    from django.test import Client
    client = Client()
    r = client.post(
        f"/api/notes/{note.pk}/send/",
        data=json.dumps({"recipient_username": recipient.username}),
        content_type="application/json",
        **auth_header(user)
    )
    assert r.status_code == 201

    copy = Note.objects.get(pk=r.json()["copy_id"])
    assert copy.owner == recipient
    copy_tags = list(copy.tags.all())
    assert len(copy_tags) == 1
    assert copy_tags[0].name == "Ideas"
    assert copy_tags[0].owner == recipient
    assert copy_tags[0].pk != sender_tag.pk


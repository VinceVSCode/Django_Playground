import pytest
from django.utils import timezone
from django.contrib.auth.models import User
from firstsite.models import Note, NoteEvent
from rest_framework.authtoken.models import Token

def auth_header(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {"HTTP_AUTHORIZATION": f"Token {token.key}"}

@pytest.mark.django_db
def test_api_analytics_daily_groups(client, user):
    # Create some events for the user
    n = Note.objects.create(title="A", content="x", owner=user)

    # Create
    NoteEvent.objects.create(user=user, note=n, action=NoteEvent.ACTION_CREATE)
    # Update
    NoteEvent.objects.create(user=user, note=n, action=NoteEvent.ACTION_UPDATE)
    # Send
    NoteEvent.objects.create(user=user, note=n, action=NoteEvent.ACTION_SEND)
    # Delete
    NoteEvent.objects.create(user=user, note=None, action=NoteEvent.ACTION_DELETE)

    r = client.get("/api/analytics/notes/?bucket=daily&actions=create,update,delete,send",
                   **auth_header(user))
    assert r.status_code == 200
    data = r.json()
    assert data["bucket"] == "daily"
    assert set(data["actions"]) == {"create","update","delete","send"}
    # There should be at least one period with counts
    assert isinstance(data["series"], dict)
    assert any(data["series"].values())

@pytest.mark.django_db
def test_analytics_html_renders(auth_client, user):
    # Minimal smoke: page renders and has expected title
    r = auth_client.get("/analytics/")
    assert r.status_code == 200
    assert b"Notes Analytics" in r.content

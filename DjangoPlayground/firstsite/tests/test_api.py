from email.policy import HTTP
from encodings.punycode import T
import json
from rest_framework.authtoken.models import Token
from firstsite.models import Note, NoteVersion

# Helper function to get auth header
def auth_header(user):
    token,_ = Token.objects.get_or_create(user=user)
    return {"HTTP_AUTHORIZATION": f"Token {token.key}"}

# Test to ensure API fetches only notes owned by the authenticated user
def test_api_list_only_own_notes(client, user, db):
    # Get user notes
    notes= Note.objects.create(title = "Mine", contents="some content", owner=user)
    # some other notes
    from django.contrib.auth.models import User
    bob = User.objects.create_user("bob", password="top_secret")
    Note.objects.create(title = "Not Mine", contents="other content", owner=bob)

    # Call API
    response = client.get("/api/notes/", **auth_header(user))
    data = response.json()
    # Check only own notes are returned
    assert response.status_code == 200
    titles = [i["title"] for i in data]
    assert "Mine" in titles and "Not Mine" not in titles

# Test API version restore
def test_api_versions_restore(client, user, note, db):
    # First we change a note with the API (ensure correct snapshots are created)
    payload = {"title": " New", "content": "Changed"}
    # call API
    response = client.put(f"/api/notes/{note.pk}/", 
                          data=json.dumps(payload), 
                          content_type="application/json", 
                          **auth_header(user)
                          )
    
    assert response.status_code == 200
    # Check one version created
    assert NoteVersion.objects.filter(note=note).count() == 1

    version =  NoteVersion.objects.filter(note=note).first()
    if version is None:
        version = NoteVersion.objects.create(
            note=note,
            title="backup title (NONE CASE)",
            content="backup content (NONE CASE)",
            updated_by=user,
        )
    # Now we restore the version with the API
    response = client.post(f"/api/notes/{note.pk}/versions/{version.pk}/restore/", **auth_header(user))
    assert response.status_code == 200
    note.refresh_from_db()
    # Check note restored
    assert note.title == version.title
    assert note.content == version.content
# Tests on lists

def test_note_list_requires_login(client):
    response =  client.get("/notes/list/")
    assert response.status_code == 302 #redirect to login
    assert "/accounts/login/" in response.headers["Location"] 

def test_notes_list_renders(auth_client):
    response = auth_client.get("/notes/list/")
    assert response.status_code == 200
    assert b"Your Notes" in response.content
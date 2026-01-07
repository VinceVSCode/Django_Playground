import pytest

@pytest.mark.smoke  # Mark this as a smoke test (quick, basic check)
@pytest.mark.django_db  # Allow this test to access the database
def test_notes_list_renders(auth_client_api):
    # Use the authenticated test client to send a GET request to the notes list page
    r = auth_client_api.get("/notes/list/")
    # Check that the response status code is 200 (OK)
    assert r.status_code == 200
    # Check that the response content contains the word "Notes"
    assert b"Notes" in r.content
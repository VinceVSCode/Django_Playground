"""P-026: htmx pagination / filtering / inline delete on the notes list."""
import pytest

from firstsite.models import Note


@pytest.fixture
def many_notes(user):
    """Enough notes to force pagination (the list paginates at 8 per page)."""
    return [
        Note.objects.create(owner=user, title=f"Note {i:02d}", content=f"Body {i}")
        for i in range(12)
    ]


# ---- pagination -------------------------------------------------------------

@pytest.mark.django_db
def test_list_plain_request_renders_full_page(auth_client, many_notes):
    r = auth_client.get("/notes/list/")
    assert r.status_code == 200
    assert b"<html" in r.content
    assert b'id="note-results"' in r.content
    assert b'class="filter-bar"' in r.content


@pytest.mark.django_db
def test_list_htmx_request_returns_results_fragment_only(auth_client, many_notes):
    r = auth_client.get("/notes/list/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert b'id="note-results"' in r.content
    # Fragment, not a whole page — no <html>, and no filter bar.
    assert b"<html" not in r.content
    assert b'class="filter-bar"' not in r.content


@pytest.mark.django_db
def test_htmx_pagination_returns_the_right_page(auth_client, many_notes):
    page2 = auth_client.get("/notes/list/?page=2", HTTP_HX_REQUEST="true")
    assert page2.status_code == 200
    # 12 notes, 8 per page -> page 2 holds 4. Default sort is -updated_at, and
    # the fixture creates Note 00..11 in order, so page 2 has the oldest four.
    assert b"Note 03" in page2.content
    assert b"Note 11" not in page2.content


@pytest.mark.django_db
def test_pager_carries_htmx_attributes(auth_client, many_notes):
    r = auth_client.get("/notes/list/")
    assert b'hx-target="#note-results"' in r.content
    assert b'hx-push-url="true"' in r.content


# ---- filtering --------------------------------------------------------------

@pytest.mark.django_db
def test_htmx_filter_applies_search(auth_client, many_notes):
    r = auth_client.get("/notes/list/?search=Note+05", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert b"Note 05" in r.content
    assert b"Note 06" not in r.content


@pytest.mark.django_db
def test_htmx_filter_with_no_matches_returns_empty_state(auth_client, many_notes):
    r = auth_client.get("/notes/list/?search=zzzznope", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert b"No notes match your filters." in r.content


# ---- inline delete confirm --------------------------------------------------

@pytest.mark.django_db
def test_delete_plain_get_still_renders_confirm_page(auth_client, note):
    r = auth_client.get(f"/notes/{note.pk}/delete/")
    assert r.status_code == 200
    assert b"<html" in r.content
    assert b"Move to Trash" in r.content


@pytest.mark.django_db
def test_delete_htmx_get_returns_inline_confirm_card(auth_client, note):
    r = auth_client.get(f"/notes/{note.pk}/delete/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert f'id="note-card-{note.pk}"'.encode() in r.content
    assert b"Move to Trash" in r.content
    assert b"Cancel" in r.content
    assert b"<html" not in r.content
    # Nothing deleted by merely asking to confirm.
    note.refresh_from_db()
    assert note.deleted_at is None


@pytest.mark.django_db
def test_delete_htmx_post_soft_deletes_and_returns_results_region(auth_client, many_notes):
    victim = many_notes[0]
    r = auth_client.post(
        f"/notes/{victim.pk}/delete/",
        data={"filter_params": ""},
        HTTP_HX_REQUEST="true",
    )
    assert r.status_code == 200
    # Whole results region comes back, so the pager stays accurate.
    assert b'id="note-results"' in r.content
    assert victim.title.encode() not in r.content

    victim.refresh_from_db()
    assert victim.deleted_at is not None  # soft delete, row kept


@pytest.mark.django_db
def test_delete_htmx_post_preserves_active_filters(auth_client, user, many_notes):
    """The re-rendered region should still be filtered the way the user had it."""
    victim = Note.objects.create(owner=user, title="Kiwi one", content="x")
    Note.objects.create(owner=user, title="Kiwi two", content="x")

    r = auth_client.post(
        f"/notes/{victim.pk}/delete/",
        data={"filter_params": "search=Kiwi"},
        HTTP_HX_REQUEST="true",
    )
    assert r.status_code == 200
    assert b"Kiwi two" in r.content      # still inside the search filter
    assert b"Kiwi one" not in r.content  # the deleted one is gone
    assert b"Note 00" not in r.content   # filter still applied, not reset


@pytest.mark.django_db
def test_note_card_fragment_endpoint_restores_a_card(auth_client, note):
    r = auth_client.get(f"/notes/{note.pk}/card/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert f'id="note-card-{note.pk}"'.encode() in r.content
    assert note.title.encode() in r.content
    assert b"<html" not in r.content


@pytest.mark.django_db
def test_note_card_fragment_rejects_other_users_note(client, django_user_model, note):
    django_user_model.objects.create_user(username="mallory", password="pass1234")
    client.login(username="mallory", password="pass1234")
    r = client.get(f"/notes/{note.pk}/card/", HTTP_HX_REQUEST="true")
    assert r.status_code == 404


@pytest.mark.django_db
def test_delete_htmx_rejects_other_users_note(client, django_user_model, note):
    django_user_model.objects.create_user(username="mallory2", password="pass1234")
    client.login(username="mallory2", password="pass1234")
    r = client.post(f"/notes/{note.pk}/delete/", HTTP_HX_REQUEST="true")
    assert r.status_code == 404
    note.refresh_from_db()
    assert note.deleted_at is None

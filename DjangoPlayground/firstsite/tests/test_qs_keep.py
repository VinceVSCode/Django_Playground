"""Regression tests for the qs_keep templatetag.

P-026 found this tag had read `context.get('requests')` (plural) since P-006,
so it always returned '' and every pager link rendered as a bare "?" — losing
the page number and all active filters on the notes list, inbox, sent and
shared-with-me pages.
"""
import pytest
from django.template import Context, Template
from django.test import RequestFactory


def render_qs_keep(query, tag="{% qs_keep page=2 %}"):
    request = RequestFactory().get(f"/notes/list/{query}")
    return Template("{% load qsp %}" + tag).render(Context({"request": request}))


def test_qs_keep_preserves_existing_filters():
    out = render_qs_keep("?search=foo&tag=3&page=1")
    assert "search=foo" in out
    assert "tag=3" in out
    assert "page=2" in out          # override applied
    assert "page=1" not in out


def test_qs_keep_is_not_empty_with_no_existing_params():
    assert render_qs_keep("") == "page=2"


def test_qs_keep_none_removes_a_key():
    out = render_qs_keep("?search=foo&tag=3", tag="{% qs_keep page=1 tag=None %}")
    assert "tag=3" not in out
    assert "search=foo" in out
    assert "page=1" in out


def test_qs_keep_without_request_in_context_returns_empty():
    """The guard still holds — no request means no querystring, not a crash."""
    assert Template("{% load qsp %}{% qs_keep page=2 %}").render(Context({})) == ""


@pytest.mark.django_db
def test_notes_list_pager_links_carry_page_and_filters(auth_client, user):
    from firstsite.models import Note
    for i in range(12):
        Note.objects.create(owner=user, title=f"QS {i:02d}", content="x")

    r = auth_client.get("/notes/list/?search=QS")
    assert r.status_code == 200
    # The bug rendered these as href="?" — assert the real querystring is there.
    assert b"page=2" in r.content
    assert b"search=QS" in r.content
    assert b'href="?"' not in r.content

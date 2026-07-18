import pytest
from firstsite.models import Note
from firstsite.templatetags.markdown_extras import markdown_filter


# --- The filter itself ---

def test_markdown_renders_basic_formatting():
    html = markdown_filter("**bold** and *italic*\n\n- item one\n- item two")
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<li>item one</li>" in html


def test_markdown_single_newlines_become_breaks():
    # Existing plain-text notes relied on linebreaksbr; nl2br keeps that behavior.
    html = markdown_filter("line one\nline two")
    assert "<br" in html


def test_markdown_strips_script_tags():
    html = markdown_filter("hello <script>alert('xss')</script> world")
    assert "<script" not in html
    assert "alert" not in html


def test_markdown_strips_event_handlers_and_bad_schemes():
    html = markdown_filter('<a href="javascript:alert(1)" onclick="alert(2)">click</a>')
    assert "javascript:" not in html
    assert "onclick" not in html


def test_markdown_links_get_safe_rel():
    html = markdown_filter("[site](https://example.com)")
    assert 'href="https://example.com"' in html
    assert "noopener" in html


def test_markdown_handles_empty_content():
    assert markdown_filter("") == ""
    assert markdown_filter(None) == ""


# --- Integration: the detail page renders markdown ---

@pytest.mark.django_db
def test_note_detail_renders_markdown(auth_client, user):
    note = Note.objects.create(
        owner=user, title="MD note", content="# Heading\n\n**important** text"
    )
    r = auth_client.get(f"/notes/{note.pk}/")
    assert r.status_code == 200
    body = r.content.decode()
    assert "<strong>important</strong>" in body
    assert 'class="markdown"' in body


@pytest.mark.django_db
def test_note_detail_escapes_html_in_content(auth_client, user):
    note = Note.objects.create(
        owner=user, title="Evil", content="<script>alert('boom')</script>"
    )
    r = auth_client.get(f"/notes/{note.pk}/")
    assert r.status_code == 200
    assert b"<script>alert" not in r.content

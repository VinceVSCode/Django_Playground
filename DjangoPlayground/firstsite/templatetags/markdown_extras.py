"""
Markdown rendering for note content (P-017).

Pipeline: raw text -> python-markdown (HTML) -> nh3 sanitizer (allow-list) -> safe string.
The database always stores the raw text; rendering happens only at display time.
nh3 is the maintained successor to bleach (which is deprecated).
"""
import markdown as md
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Only these tags survive sanitizing. Anything else (script, style, iframe,
# event handlers, ...) is stripped, which is what protects us from XSS.
ALLOWED_TAGS = {
    "p", "br", "hr",
    "strong", "em", "del", "code", "pre",
    "blockquote",
    "ul", "ol", "li",
    "h1", "h2", "h3", "h4",
    "a",
    "table", "thead", "tbody", "tr", "th", "td",
}

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
}


@register.filter(name="markdown")
def markdown_filter(text):
    """
    Usage: {{ note.content|markdown }}
    Renders Markdown to sanitized HTML. Single newlines become <br> (nl2br)
    so existing plain-text notes keep their line breaks.
    """
    html = md.markdown(
        text or "",
        extensions=["fenced_code", "sane_lists", "nl2br", "tables"],
    )
    clean = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
    return mark_safe(clean)

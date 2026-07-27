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

@pytest.mark.django_db
def test_analytics_html_includes_chart_markup(auth_client, user):
    # P-019: the chart mount point, its controls, the JS file, and the
    # no-JS fallback message must all be present on the page.
    r = auth_client.get("/analytics/")
    body = r.content.decode()
    assert 'id="chart"' in body
    assert 'id="fromDate"' in body and 'id="toDate"' in body and 'id="clearRange"' in body
    assert 'id="legend"' in body
    assert "analytics_chart.js" in body
    assert "Enable JavaScript to see the chart" in body

@pytest.mark.django_db
def test_api_analytics_periods_are_full_dates_for_every_bucket(auth_client, user):
    # The chart's client-side date-range filter relies on every bucket
    # reporting a full "YYYY-MM-DD" period key (see analytics_chart.js).
    note = Note.objects.create(title="A", content="x", owner=user)
    NoteEvent.objects.create(user=user, note=note, action=NoteEvent.ACTION_CREATE)

    for bucket in ["daily", "weekly", "monthly", "yearly"]:
        r = auth_client.get(f"/api/analytics/notes/?bucket={bucket}")
        assert r.status_code == 200
        series = r.json()["series"]
        assert series, f"expected at least one period for bucket={bucket}"
        for period in series:
            assert len(period) == 10 and period[4] == "-" and period[7] == "-", (
                f"bucket={bucket} period={period!r} is not a full YYYY-MM-DD date"
            )

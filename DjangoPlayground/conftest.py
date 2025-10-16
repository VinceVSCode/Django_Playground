import pytest
from django.contrib.auth.models import User
from firstsite.models import Note, Tag

@pytest.fixture
def user(db):
    """
    Create a normal user we can log in with.
    'db' fixture gives a fresh test database.
    """
    return User.objects.create_user(username="alice", password="pass1234")

@pytest.fixture
def auth_client(client, user):
    """
    Django test client with the above user already logged in.
    Use this to check the HTML views that require login.
    """
    client.login(username="alice", password="pass1234")
    return client

@pytest.fixture
def tag(user):
    """
    A sample Tag belonging to 'alice'.
    """
    return Tag.objects.create(name="Work", owner=user)

@pytest.fixture
def note(user):
    """
    A sample Note belonging to 'alice'.
    """
    return Note.objects.create(title="Hello", content="World", owner=user)

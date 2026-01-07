import pytest
from django.contrib.auth.models import User
from firstsite.models import Note, Tag
from django.test.client import Client
from rest_framework.authtoken.models import Token

@pytest.fixture
def user(db):
    """
    Create a normal user we can log in with.
    'db' fixture gives a fresh test database.
    """
    return User.objects.create_user(username="alice", password="pass1234")

@pytest.fixture
def auth_client_login(client, user):
    """
    Django test client with the above user already logged in.
    Use this to check the HTML views that require login.
    """
    client.login(username="alice", password="pass1234")
    return client

@pytest.fixture
def auth_client_api(db, user):
    """
    Django client with DRF Token auth header set for 'user'.
    Use for API tests.
    """
    token, _ = Token.objects.get_or_create(user=user)
    c = Client()
    c.defaults['HTTP_AUTHORIZATION'] = f"Token {token.key}"
    return c

@pytest.fixture
def tag(user):
    """
    A sample Tag belonging to 'alice'.
    """
    return Tag.objects.create(name="Work", owner=user)

@pytest.fixture
def note(db, user):
    """
    A sample Note belonging to 'alice'.
    """
    return Note.objects.create(title="Hello", content="World", owner=user)

@pytest.fixture
def client():
    # plain Django test client
    return Client()

@pytest.fixture
def another_user(db):
    """
    Create another user for testing interactions.
    """
    return User.objects.create_user(username="bob", password="pass5678")

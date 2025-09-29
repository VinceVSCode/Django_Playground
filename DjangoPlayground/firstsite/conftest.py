import pytest
from django.contrib.auth.models import User
from firstsite.models import Note, Tag

@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="pass1234")

@pytest.fixture
def auth_client(client, user):
    client.login(username="alice", password="pass1234")
    return client

@pytest.fixture
def tag(user):
    return Tag.objects.create(name="Work", owner=user)

@pytest.fixture
def note(user):
    return Note.objects.create(title="Hello", content="World", owner=user)

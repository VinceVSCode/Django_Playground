import pytest
from django.db import IntegrityError
from firstsite.models import Note, Tag

def test_note_defaults(user):
    note = Note.object.create(title= "Test123 Note", content = "C", owner=user)
    assert note.is_pinned is False
    assert note.is_archived is False
    assert note.created_at and note.updated_at

def test_tag_unique_per_user(user,db):
    Tag.objects.create(name= "Ideas", owner=user)
    with pytest.raises(IntegrityError):
        Tag.objects.create(name= "Ideas", owner=user ) #unique_together constrain
        
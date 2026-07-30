from typing import Any
from django.contrib.auth.models import AnonymousUser
from .models import NoteEvent, Tag


def copy_tags_for_recipient(note: Any, copy: Any, recipient: Any) -> None:
    """
    Attach tags to a sent-note copy without leaking the sender's Tag rows.

    `copy.tags.set(note.tags.all())` would attach the *sender's* Tag rows to
    the recipient's note, which the recipient can't see or manage (tag views
    filter by owner) and which breaks their `?untagged=1` filter. Instead,
    get_or_create a same-named Tag owned by the recipient for each tag on the
    original note, and attach those.
    """
    tags = [
        Tag.objects.get_or_create(owner=recipient, name=tag.name)[0]
        for tag in note.tags.all()
    ]
    copy.tags.set(tags)


def attach_actor(instance: Any, user: Any) -> None:
    """
    Attaches the user as the actor to the given instance for auditing purposes.
    This serves the purpose of tracking who made changes to an object.
    """
    if user and not isinstance(user, AnonymousUser):
        setattr(instance, '_actor', user)

def log_note_event(user: Any, note: Any, action: str) -> NoteEvent | None:
    """
    Central function that audit events.
    - Stores FKs (user/note) but also denormalized snapshots (actor_username, note_title)
      so analytics survive deletions/renames.
    """
    username =  None
    if user and not isinstance(user, AnonymousUser):
        username =  getattr(user, 'username', None)

    title = None
    if note is not None:
        title = getattr(note, 'title', None)
    
    return NoteEvent.objects.create(
        user=user if username else None,
        note=note if note else None,
        actor_username=username,
        note_title=title,
        action=action,
    )
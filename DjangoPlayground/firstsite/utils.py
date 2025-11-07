from typing import Any
from django.contrib.auth.models import AnonymousUser
from .models import NoteEvent 
def attach_actor(instance: Any, user: Any) -> None:
    """
    Attaches the user as the actor to the given instance for auditing purposes.
    This serves the purpose of tracking who made changes to an object.
    """
    if user and not isinstance(user, AnonymousUser):
        setattr(instance, '_actor', user)

def log_note_event(user: Any, note: Any, action: str) -> NoteEvent | None:
    """
    Central function that creates analytics/audit events.
    - user: the acting user (ignored if None/Anonymous)
    - note: the related Note instance or None (for deletes)
    - action: one of NoteEvent.ACTION_*
    """

    if user and not isinstance(user, AnonymousUser):
        return NoteEvent.objects.create(user=user,note=note,action=action)
    
    return None
from typing import Any
from django.contrib.auth.models import AnonymousUser

def attach_actor(instance: Any, user: Any) -> None:
    """
    Attaches the user as the actor to the given instance for auditing purposes.
    This serves the purpose of tracking who made changes to an object.
    """
    if user and not isinstance(user, AnonymousUser):
        setattr(instance, '_actor', user)
    
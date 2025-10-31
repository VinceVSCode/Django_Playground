from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AnonymousUser
from .middleware import get_current_user
from .models import Note, NoteEvent
import logging

log = logging.getLogger(__name__)
# Helper: I will attach request.user to the Note instance before saving in the view.
# This is a common pattern to access the user in signals. Also a safe fallback to AnonymousUser.


def _actor_for(instance):
    # Prefer the explicitly set _actor on the instance (from the view), else use the current user from middleware.
    user = getattr(instance, '_actor', None) or get_current_user()
    return None if isinstance(user, AnonymousUser) else user

@receiver(post_save, sender=Note)
def log_note_save(sender, instance: Note, created,**kwargs):
    actor =  _actor_for(instance)
    log.warning("post_save Note: created=%s, actor=%r, note_id=%s", created, getattr(actor,'username',None), instance.pk)

    if not actor:
        return NoteEvent.objects.create(
            user =  actor,
            note=  instance,
            action = NoteEvent.ACTION_CREATE if created else NoteEvent.ACTION_UPDATE
        )
    
@receiver(post_delete, sender=Note)
def log_note_delete(sender, instance: Note, **kwargs):
    actor =  _actor_for(instance)
    log.warning("post_delete Note: actor=%r, note_id=%s", getattr(actor,'username',None), instance.pk)
    
    if not actor:
        return NoteEvent.objects.create(
            user =  actor,
            note=  None, # Note is deleted, but we keep event record.
            action = NoteEvent.ACTION_DELETE
        )
        
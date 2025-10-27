from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AnonymousUser
from .models import Note, NoteEvent

# Helper: I will attach request.user to the Note instance before saving in the view.
# This is a common pattern to access the user in signals. Also a safe fallback to AnonymousUser.

def _actor_for(instance):
    return getattr(instance, '_actor', None)

@receiver(post_save, sender=Note)
def log_note_save(sender, instance: Note, created,**kwargs):
    actor =  _actor_for(instance)
    if isinstance(actor, AnonymousUser) or actor is None:
        return NoteEvent.objects.create(
            user =  actor,
            note=  instance,
            action = NoteEvent.ACTION_CREATE if created else NoteEvent.ACTION_UPDATE
        )
    
@receiver(post_delete, sender=Note)
def log_note_delete(sender, instance: Note, **kwargs):
    actor =  _actor_for(instance)
    if isinstance(actor, AnonymousUser) or actor is None:
        return NoteEvent.objects.create(
            user =  actor,
            note=  None, # Note is deleted, but we keep event record.
            action = NoteEvent.ACTION_DELETE
        )
        
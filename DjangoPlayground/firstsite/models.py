from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# Note model
class Note(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length = 100)
    content =  models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    tags = models.ManyToManyField('Tag', blank=True)
    
    def __str__(self):
        return self.title


# Tag model
class Tag(models.Model):
    name = models.CharField(max_length=16)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('owner', 'name')  # Ensure unique tag names per user

    def __str__(self):
        return self.name
    
# Note Version model
class NoteVersion(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE,related_name = 'versions')
    title = models.CharField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey( User,on_delete=models.SET_NULL, null=True, blank=True, related_name='note_versions')
    
    def __str__(self):
        return f"Version of {self.note.title} at {self.timestamp}"
    
# NoteSend Model
class NoteSend (models.Model):
    """
    Log that a note was sent (copy) from one user to another.
    Used for analytics and tracking.
    """
    original_note = models.ForeignKey(Note, on_delete=models.SET_NULL, null=True, blank=True, related_name='sends')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes_sent')
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notes_received')
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: ({self.original_note_id})"
    
# NoteEvent
class NoteEvent(models.Model):
    """
    Generic audit trail for analytics: create/update/delete/send.
    """
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_SEND = 'send'
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_SEND, 'Send'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    note = models.ForeignKey('Note', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)

    # Snapshots for presentation purposes
    actor_username = models.CharField(max_length=150, null=True, blank=True)
    note_title     = models.CharField(max_length=255, null=True, blank=True)

    action = models.CharField(max_length=10, choices=ACTION_CHOICES,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)

    def __str__(self):
        # Format: "actor action note @ timestamp", preserving info if user or note is deleted
        who  = self.actor_username or (self.user.username if self.user_id else "unknown")
        what = self.note_title or (getattr(self.note, "title", None) or "note")
        return f"{who} {self.action} {what} @ {self.created_at:%Y-%m-%d %H:%M}"
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# Note model
class Note(models.Model):
    title = models.CharField(max_length = 100)
    content =  models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', blank=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    # tags
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
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='versions')
    title = models.CharField(max_length=100)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Version of {self.note.title} at {self.timestamp}"
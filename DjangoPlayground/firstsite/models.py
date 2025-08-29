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
    
    # tags
    tags = models.ManyToManyField('Tag', blank=True)
    
    def __str__(self):
        return self.title


# Tag model
class Tag(models.Model):
    name = models.CharField(max_length=16)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
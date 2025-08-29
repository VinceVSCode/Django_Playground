from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# Note model
class Note(models.Model):
    title = models.CharField(max_length = 200)
    content =  models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title


# Tag model
class Tag(models.Model):
    name = models.CharField(max_length=16)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
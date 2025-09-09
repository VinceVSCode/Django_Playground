from django.contrib import admin
from .models import Note, NoteVersion, Tag

# Register your models here.
admin.site.register(Note)
admin.site.register(Tag)
admin.site.register(NoteVersion)

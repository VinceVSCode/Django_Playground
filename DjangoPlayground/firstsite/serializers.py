from rest_framework import serializers
from .models import Note, Tag

class NoteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, # a note can have multiple tags
        queryset=Tag.objects.all(), # to be overidden in the view. 
        required = False # tags are optional
        )

    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'created_at', 'updated_at', 'tags']
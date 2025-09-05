from rest_framework import serializers
from .models import Note, Tag

# Serializer for the Note model
class NoteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, # a note can have multiple tags
        queryset=Tag.objects.all(), # to be overidden in the view. 
        required = False # tags are optional
        )

    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'created_at', 'updated_at', 'tags','is_pinned', 'is_archived']

# Serializer for the Tag model
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id'] # ID is read-only, so we can assign owner manually via API.
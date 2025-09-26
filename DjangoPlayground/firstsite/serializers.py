from rest_framework import serializers
from .models import Note, Tag, NoteVersion

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

# Serializer for the NoteVersion model
class NoteVersionSerializer(serializers.ModelSerializer):
    # Custom field to get the username of the user who updated the note
    updated_by_username =serializers.SerializerMethodField()

    class Meta:
        model = NoteVersion
        # Include all fields from the NoteVersion model
        fields = ['id', 'title', 'content', 'timestamp', 'updated_at', 'updated_by','updated_by_username']
        # Make certain fields read-only as they are auto-generated.
        read_only_fields = ['timestamp', 'updated_at', 'updated_by']
        
    def get_updated_by_username(self, obj):
        # Safely return the username of the user who made the update, or None if not available
        return getattr(obj.updated_by, 'username', None)
from django.urls import path
from .views import api_note_detail, api_user_notes, create_note, hello_world, user_notes ,api_list_tags, note_list_view

urlpatterns = [
    path('hello/', hello_world, name='hello_world'), # Maps the root URL to the hello_world view. Basically /firstsite/ will call the hello_world function.

    # User notes
    path('notes/',user_notes, name = "user_notes"),
    path('notes/create/', create_note, name='create_note'), # Maps the URL /firstsite/notes/create/ to the create_note view.
    path('notes/list/', note_list_view, name='note_lists'), # Maps the URL /firstsite/notes/list/ to the note_lists_view.

    # API note endpoints
    path('api/notes/', api_user_notes, name='api_user_notes'), # API endpoint to get user notes
    #path('api/notes/create/', api_user_notes, name='api_create_note'), # API endpoint to create a new note
    path('api/notes/<int:pk>/', api_note_detail, name='api_note_detail'), # API endpoint to get a specific note

    # API tag endpoints
    path('api/tags/', api_list_tags, name='api_list_tags'), # API endpoint to list all tags
]
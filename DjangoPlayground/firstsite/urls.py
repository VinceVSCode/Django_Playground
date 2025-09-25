from django.urls import path
from .views import api_note_detail, api_user_notes, create_note, hello_world, note_lists_view, note_restore_version, tag_create_view, user_notes ,api_list_tags, note_detail_view, note_update_view, note_delete_view,note_toggle_pin, note_toggle_archive, tag_list_view, tag_update_view, tag_delete_view



urlpatterns = [
    path('hello/', hello_world, name='hello_world'), # Maps the root URL to the hello_world view. Basically /firstsite/ will call the hello_world function.

    # User notes
    path('notes/',user_notes, name = "user_notes"),
    path('notes/create/', create_note, name='create_note'), # Maps the URL /firstsite/notes/create/ to the create_note view.
    path('notes/list/', note_lists_view, name='note_lists'), # Maps the URL /firstsite/notes/list/ to the note_lists_view.
    path('notes/<int:pk>/', note_detail_view, name='note_detail'), # Maps the URL /firstsite/notes/<int:pk>/ to the note_detail_view.
    path('notes/<int:pk>/edit/', note_update_view, name='note_edit'),
    path('notes/<int:pk>/delete/', note_delete_view, name='note_delete'),
    path('notes/<int:pk>/toggle-pin/', note_toggle_pin, name='note_toggle_pin'), # Toggle pin status of a note
    path('notes/<int:pk>/toggle-archive/', note_toggle_archive, name='note_toggle_archive'), # Toggle archive status of a note
    path('notes/<int:pk>/versions/<int:version_id>/restore/', note_restore_version, name='note_restore_version'), # View note versions

    # Tag views
    path('tags/', tag_list_view, name='tag_list'),
    path('tags/new/', tag_create_view, name='tag_create'),
    path('tags/<int:pk>/edit/', tag_update_view, name='tag_edit'),
    path('tags/<int:pk>/delete/', tag_delete_view, name='tag_delete'),

    # API note endpoints
    path('api/notes/', api_user_notes, name='api_user_notes'), # API endpoint to get user notes
    #path('api/notes/create/', api_user_notes, name='api_create_note'), # API endpoint to create a new note
    path('api/notes/<int:pk>/', api_note_detail, name='api_note_detail'), # API endpoint to get a specific note

    # API tag endpoints
    path('api/tags/', api_list_tags, name='api_list_tags'), # API endpoint to list all tags
]
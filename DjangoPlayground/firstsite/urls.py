from django.urls import path
from firstsite import views as v


urlpatterns = [
    path('hello/', v.hello_world, name='hello_world'), # Maps the root URL to the hello_world view. Basically /firstsite/ will call the hello_world function.

    # User notes
    path('notes/', v.user_notes, name = "user_notes"),
    path('notes/create/', v.create_note, name='create_note'), # Maps the URL /firstsite/notes/create/ to the create_note view.
    path('notes/list/', v.note_lists_view, name='note_lists'), # Maps the URL /firstsite/notes/list/ to the note_lists_view.
    path('notes/<int:pk>/', v.note_detail_view, name='note_detail'), # Maps the URL /firstsite/notes/<int:pk>/ to the note_detail_view.
    path('notes/<int:pk>/send/', v.note_send_view, name='note_send'), # Send note to another user functionality
    path('notes/<int:pk>/edit/', v.note_update_view, name='note_edit'),
    path('notes/<int:pk>/delete/', v.note_delete_view, name='note_delete'),
    path('notes/<int:pk>/toggle-pin/', v.note_toggle_pin, name='note_toggle_pin'), # Toggle pin status of a note
    path('notes/<int:pk>/toggle-archive/', v.note_toggle_archive, name='note_toggle_archive'), # Toggle archive status of a note
    path('notes/<int:pk>/versions/<int:version_id>/restore/', v.note_restore_version, name='note_restore_version'), # View note versions

    # Tag views
    path('tags/', v.tag_list_view, name='tag_list'),
    path('tags/new/', v.tag_create_view, name='tag_create'),
    path('tags/<int:pk>/edit/', v.tag_update_view, name='tag_edit'),
    path('tags/<int:pk>/delete/', v.tag_delete_view, name='tag_delete'),

    # API note endpoints
    path('api/notes/', v.api_user_notes, name='api_user_notes'), # API endpoint to get user notes
    path('api/analytics/notes/', v.api_note_analytics, name='api_note_analytics'),
    #path('api/notes/create/', api_user_notes, name='api_create_note'), # API endpoint to create a new note
    path('api/notes/<int:pk>/', v.api_note_detail, name='api_note_detail'), # API endpoint to get a specific note
    path('api/notes/<int:pk>/send/', v.api_note_send, name='api_note_send'), 
    path('api/notes/<int:pk>/versions/', v.api_note_versions, name='api_note_versions'),
    path('api/notes/<int:pk>/versions/<int:version_id>/restore/', v.api_note_restore_version, name='api_note_restore_version'),
    path('api/notes/<int:pk>/versions/<int:version_id>/', v.api_note_version_detail, name='api_note_version_detail'),
    
    # API tag endpoints
    path('api/tags/', v.api_list_tags, name='api_list_tags'), # API endpoint to list all tags
]
from django.urls import path
from .views import hello_world, user_notes

urlpatterns = [
    path('hello/', hello_world, name='hello_world'), # Maps the root URL to the hello_world view. Basically /firstsite/ will call the hello_world function.
    path('notes/',user_notes, name = "user_notes"),
] 
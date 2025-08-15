from django.urls import path
from .views import hello_world

urlpatterns = [
    path('', hello_world, name='hello_world'), # Maps the root URL to the hello_world view. Basically /firstsite/ will call the hello_world function.
] 
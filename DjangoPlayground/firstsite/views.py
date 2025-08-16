from django.shortcuts import render, redirect
from .models import Note
from .forms import NoteForm
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import NoteSerializer
# Create your views here.

def hello_world(request):
    if request.user.is_authenticated:
        name = request.user.username
        message = f"Hello, {name}! Welcome back."
    else:
        name = "Temporary User"
        message = f"Hello, {name}! Please consider logging in."

    context = {
        'name': name,
        'message': message
    }
    return render(request, 'firstsite/hello.html', context)

# API endpoint to get user notes
@login_required
def user_notes(request):
    notes = Note.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'firstsite/user_notes.html', {'notes': notes})

# API endpoint to create a new note
@login_required
def create_note(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            return redirect('user_notes') # name defined in urls.py
    else:
        form = NoteForm()

    return render(request, 'firstsite/create_note.html', {'form': form})

# API endpoint to create a new note
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_notes(request):
    notes = Note.objects.filter(owner=request.user).order_by('-created_at')
    serializer = NoteSerializer(notes, many=True)
    return Response(serializer.data)
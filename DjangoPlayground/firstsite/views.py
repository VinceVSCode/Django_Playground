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
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_user_notes(request):
    if request.method == 'GET':
        """
        Retrieve all notes for the authenticated user.
        """
        notes = Note.objects.filter(owner = request.user).order_by('-created_at')
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """
        Create a new note for the authenticated user.
        """
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():

            note = serializer.save(owner=request.user)
            # note = serializer.save(commit=False)
            # note.owner = request.user
            # note.save()
            return Response(NoteSerializer(note).data, status=201)
        return Response(serializer.errors, status=400)

# API endpoint to retrieve a specific note
@api_view(['GET, PUT, DELETE'])
@permission_classes([IsAuthenticated])
def api_note_detail(request, pk):
    """
    Retrieve a specific note for the authenticated user.
    """
    try:
        # Look up the note by primary key (pk) and ensure it belongs to the authenticated user
        note = Note.objects.get(pk=pk, owner=request.user)
    except Note.DoesNotExist:
        # Handle the case where the note does not exist
        return Response({'error': 'Note not found'}, status=404)

    # The NoteExists. Read a single note.
    if request.method == 'GET':
        # Retrieve the note details
        serializer = NoteSerializer(note)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        #  Update the note details
        serializer = NoteSerializer(note, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        # Delete the note
        note.delete()
        return Response(status=204)
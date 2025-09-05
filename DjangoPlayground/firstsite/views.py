from django.shortcuts import render, redirect
from .models import Note, Tag
from .forms import NoteForm
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import NoteSerializer , TagSerializer
from django.db.models import Q
"""
To generate tokens for users, you can use the following command in your terminal:
python manage.py drf_create_token 'your_username'
then use the generated token in your API requests as follows:
Authorization: Token your_generated_token

Have fun!
"""
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
        Retrieve all notes for the authenticated user and support tag filtering.
        """
        # Get the tag ID from the query parameters
        tag_id = request.query_params.get('tag')

        # Support search with no taggs.
        untagged = request.query_params.get('untagged') == '1'
        
        # Query search 
        search_query = request.query_params.get('search')

        # Filter notes by tag if tag_id is provided
        notes = Note.objects.filter(owner=request.user)

        # pinned requests, we need to have 'notes' defined before we filter it.
        pinned = request.query_params.get('pinned')

        if pinned == '1':
            notes = notes.filter(is_pinned=True)
        elif pinned == '0':
            notes = notes.filter(is_pinned=False)


        if tag_id:
            # Filter notes by tag if tag_id is provided
            try:
                tag = Tag.objects.get(id=tag_id, owner=request.user)
                notes = notes.filter(tags=tag)
            except Tag.DoesNotExist:
                notes = Note.objects.none()
        elif untagged:
            notes = notes.filter(tags__isnull=True)

        if search_query:
            notes = notes.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
                )

        # Lastly, order notes by creation date (newest first)
        notes = notes.order_by('-created_at')
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """
        Create a new note for the authenticated user.
        """
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            # Save the note with the authenticated user as the owner
            note = serializer.save(owner=request.user)
            #Attach tags (if any)
            tags = request.data.get('tags', [])
            if tags:
                note.tags.set(Tag.objects.filter(id__in=tags, owner=request.user))

            # Return the created note data
            return Response(NoteSerializer(note).data, status=201)
        # If the serializer is not valid, return the errors
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
            # Optional: update tags
            tags = request.data.get('tags', [])
            note.tags.set(Tag.objects.filter(id__in=tags, owner=request.user))
            
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        # Delete the note
        note.delete()
        return Response(status=204)
    
# Tag API endpoint

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_list_tags(request):
    """
    List all tags for the authenticated user.
    """
    if request.method == 'GET':

        tags = Tag.objects.filter(owner=request.user).order_by('name') # Order alphabetically, so as to be better in the eyes.
        serializer = TagSerializer(tags, many=True)  # Serialize the list of tags
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Create a new tag for the authenticated user.
        serializer = TagSerializer(data=request.data)

        # Validate the serializer
        if serializer.is_valid():
            tag = serializer.save(owner=request.user)

            return Response(TagSerializer(tag).data, status=201) # Return the created tag data and proper status

        return Response(serializer.errors, status=400) # Return the errors if the serializer is not valid
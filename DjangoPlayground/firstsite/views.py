from django.shortcuts import render, redirect, get_object_or_404
from .models import Note, NoteVersion, Tag
from .forms import NoteForm
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.http import require_POST
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import NoteSerializer , TagSerializer
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator

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

# Redirect to notes list if logged in, else to login page.
def home(request):
    if request.user.is_authenticated:
        return redirect('note_lists')  # to your notes list
    return redirect('login')           # to /accounts/login/

# API endpoint to get user notes
@login_required
def user_notes(request):
    notes = Note.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'firstsite/user_notes.html', {'notes': notes})

# View to list notes for the logged-in user. Render a template with the notes.
@login_required
def note_lists_view(request):
    # Query params
    tag_id = request.GET.get('tag')                 # e.g. ?tag=3
    untagged = request.GET.get('untagged') == '1'   # e.g. ?untagged=1
    search = request.GET.get('search')              # e.g. ?search=foo
    pinned = request.GET.get('pinned')              # '1', '0', or None
    archived = request.GET.get('archived')          # '1', '0', or None

    # Base queryset: only current user's notes
    notes = Note.objects.filter(owner=request.user)

    # Tag filtering (exclusive with untagged)
    if tag_id:
        notes = notes.filter(tags__id=tag_id,tags_owner=request.user)
    elif untagged:
        notes = notes.filter(tags__isnull=True)

    # Pinned filtering
    if pinned == '1':
        notes = notes.filter(is_pinned=True)
    elif pinned == '0':
        notes = notes.filter(is_pinned=False)
    
    # Archived filtering
    if archived == '1':
        notes = notes.filter(is_archived=True)
    elif archived == '0':
        notes = notes.filter(is_archived=False)
    
    # Search filtering
    if search:
        notes = notes.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )

    # Order notes by creation date (newest first)
    notes = notes.order_by('-is_pinned', '-updated_at').distinct()

    # Paginate the notes shown, 8 per page.
    paginator = Paginator(notes, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    #Keep filters in pagination links
    params = request.GET.copy()
    params.pop('page', None)  # remove existing page parameter
    querystring = params.urlencode() # for example tag=3&search=foo




    # Order the tag dropdown alphabetically
    tags = Tag.objects.filter(owner=request.user).order_by('name')

    ctx= {
        'tags': tags,
        'values': request.GET,
        'page_obj': page_obj,
        'querystring': querystring,
        'notes':page_obj.object_list,  # the notes for the current page
    }
    return render(request, 'firstsite/note_list.html', ctx)

# Toggle pin status of a note
@login_required
@require_POST
def note_toggle_pin(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    note.is_pinned = not note.is_pinned
    note.save(update_fields=['is_pinned', 'updated_at'])
    messages.success(request, "Note pinned." if note.is_pinned else "Note unpinned.")
    return redirect(request.POST.get('next') or 'note_lists')

# Toggle archive status of a note
@login_required
@require_POST
def note_toggle_archive(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    note.is_archived = not note.is_archived
    note.save(update_fields=['is_archived', 'updated_at'])
    messages.success(request, "Note archived." if note.is_archived else "Note restored.")
    return redirect(request.POST.get('next') or 'note_lists')

@login_required
def note_detail_view(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    return render(request, 'firstsite/note_detail.html', {'note': note})


# API endpoint to create a new note
@login_required
def create_note(request):
    # check if it is a post.
    if request.method == "POST":
        form = NoteForm(request.POST, user=request.user)  # Pass the user to the form
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            # sent a success message
            messages.success(request, "Note created successfully!")
            form.save_m2m()  # save selected tags
            # Redirect to the note list view after creation
            return redirect('note_lists')
    else:
        form = NoteForm(user=request.user)
    return render(request, "firstsite/create_note.html", {"form": form})

# API endpoint to edit note
@login_required
def edit_note (request, pk):
    note = get_object_or_404(Note,pk=pk, owner=request.user)
    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        form.fields["tags"].queryset = Tag.objects.filter(owner=request.user)

        if form.is_valid():
            # Snapshot current state before updating (versioning)
            NoteVersion.objects.create(
                note=note,
                title=note.title,
                content=note.content,
                updated_by=request.user,
            )
            form.save()  # saves fields + m2m
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm(instance=note)
        form.fields["tags"].queryset = Tag.objects.filter(owner=request.user)

    return render(request, "firstsite/edit_note.html", {"form": form, "note": note})
# API endpoint to update note
@login_required
def note_update_view(request, pk):
    """
    Edit an existing note owned by the current user.
    We use NoteForm and keep the tag choices limited to the user's tags. (for now)
    """

    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == "POST":
        form = NoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            # Snapshot current state before updating (versioning)
            NoteVersion.objects.create(
                note=note,
                title=note.title,
                content=note.content,
                updated_by=request.user,
            )
            form.save()  # saves fields + m2m
            messages.success(request, "Note updated successfully!")
            return redirect("note_detail", pk=note.pk)
    else:
        form = NoteForm(instance=note, user=request.user)
    return render(request, "firstsite/edit_note.html", {"form": form, "note": note})

# API endpoint to delete note
@login_required
def note_delete_view(request, pk):
    """
    Confirm + delete flow with CSRF protection.
    GET -> show confirmation, POST -> delete then redirect to list.
    """
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == "POST":
        note.delete()
        messages.success(request, "Note deleted successfully.")
        return redirect("note_lists")
    return render(request, "firstsite/confirm_delete.html", {"note": note})

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
            
        # achieved via query parameters.
        archived = request.query_params.get('archived')

        if archived == '1':
            notes = notes.filter(is_archived=True)
        elif archived == '0':
            notes = notes.filter(is_archived=False)


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
            # First save the current version before updating
            NoteVersion.objects.create(
                note=note,
                title=note.title,
                content=note.content,
                updated_by= request.user

            )
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
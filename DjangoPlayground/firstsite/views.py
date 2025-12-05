from django.shortcuts import render, redirect, get_object_or_404

from .utils import attach_actor, log_note_event
from .models import Note, NoteVersion, Tag, NoteSend, NoteEvent
from .forms import NoteForm, TagForm, SendNoteForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.http import require_POST
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import NoteSerializer , TagSerializer, NoteVersionSerializer
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear


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
        notes = notes.filter(tags__id=tag_id,tags__owner=request.user)
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

    # ---- Date range filtering ----
    # Choose which field to filter: updated_at (default) or created_at
    date_field = request.GET.get('date_field', 'updated')  # 'updated' | 'created'
    field_map = {'updated': 'updated_at', 'created': 'created_at'}
    target_field = field_map.get(date_field, 'updated_at')

    from_str = request.GET.get('from')  # YYYY-MM-DD
    to_str   = request.GET.get('to')    # YYYY-MM-DD

    from_date = parse_date(from_str) if from_str else None
    to_date   = parse_date(to_str) if to_str else None

    if from_date:
        notes = notes.filter(**{f'{target_field}__date__gte': from_date})
    if to_date:
        notes = notes.filter(**{f'{target_field}__date__lte': to_date})


    # ---- Sorting (defaults: updated description) ----
    sort = request.GET.get('sort', 'updated')   # 'updated' | 'created' | 'title'
    direction = request.GET.get('dir', 'desc')  # 'asc' | 'desc'
    field_map = {
        'updated': 'updated_at',
        'created': 'created_at',
        'title':   'title',
    }
    order_field = field_map.get(sort, 'updated_at')
    prefix = '' if direction == 'asc' else '-'
    # Keep pinned notes first; then apply chosen ordering
    notes = notes.order_by('-is_pinned', f'{prefix}{order_field}').distinct()


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
    attach_actor(note, request.user)
    note.save(update_fields=['is_pinned', 'updated_at'])
    messages.success(request, "Note pinned." if note.is_pinned else "Note unpinned.")
    return redirect(request.POST.get('next') or 'note_lists')

# Toggle archive status of a note
@login_required
@require_POST
def note_toggle_archive(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    note.is_archived = not note.is_archived
    attach_actor(note, request.user)
    note.save(update_fields=['is_archived', 'updated_at'])
    messages.success(request, "Note archived." if note.is_archived else "Note restored.")
    return redirect(request.POST.get('next') or 'note_lists')

@login_required
def note_detail_view(request, pk):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    versions = note.versions.order_by('-timestamp')  # related_name='versions' on NoteVersion
    return render(request, 'firstsite/note_detail.html', {'note': note,'versions': versions})


# API endpoint to create a new note
@login_required
def create_note(request):
    # check if it is a post.
    if request.method == "POST":
        form = NoteForm(request.POST, user=request.user)  # Pass the user to the form
        if form.is_valid():
            
            note = form.save(commit=False)
            note.owner = request.user
            attach_actor(note, request.user)
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
            # signal who made the change
            attach_actor(note, user=request.user)
            
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
            # signal who made the change
            attach_actor(note, user=request.user)
            form.save()  # saves fields + m2m

            # update event log
            #log_note_event(request.user, note, NoteEvent.ACTION_UPDATE)

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
        attach_actor(note, request.user)
        # delete first or log first? let's delete first. (don't know if it matters)
        note.delete()
        #log_note_event(request.user, None, NoteEvent.ACTION_DELETE)
        messages.success(request, "Note deleted successfully.")

        return redirect("note_lists")
    return render(request, "firstsite/confirm_delete.html", {"note": note})

# Note Restore Version
@login_required
@require_POST
def note_restore_version(request, pk, version_id):
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    version =  get_object_or_404(NoteVersion, pk=version_id, note=note)
    # Snapshot current state before restoring (so we don't lose it)
    NoteVersion.objects.create(
        note=note,
        title=note.title,
        content=note.content,
        updated_by=request.user,
    )

    # Restore the note's content from the selected version
    note.title = version.title
    note.content = version.content
    attach_actor(note, request.user)
    note.save(update_fields=['title', 'content', 'updated_at'])
    messages.success(request, "Version restored.")
    return redirect("note_detail", pk=note.pk)

# Tag views
@login_required
def tag_list_view(request):
    tags = Tag.objects.filter(owner=request.user).order_by('name')
    return render(request, 'firstsite/tag_list.html', {'tags': tags})

# Create a new tag
@login_required
def tag_create_view(request):
    if request.method == 'POST':
        form = TagForm(request.POST, user=request.user)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.owner = request.user
            tag.save()
            messages.success(request, "Tag created.")
            return redirect('tag_list')
    else:
        form = TagForm(user=request.user)
    return render(request, 'firstsite/tag_form.html', {'form': form, 'title': 'New Tag'})

# Update an existing tag
@login_required
def tag_update_view(request, pk):
    tag = get_object_or_404(Tag, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag, user=request.user)
        if form.is_valid():
            note = get_object_or_404(Note, pk=pk, owner=request.user)
            form.save()
            messages.success(request, "Tag renamed.")
            return redirect('tag_list')
    else:
        form = TagForm(instance=tag, user=request.user)
    return render(request, 'firstsite/tag_form.html', {'form': form, 'title': 'Rename Tag'})

# Delete a tag
@login_required
def tag_delete_view(request, pk):
    tag = get_object_or_404(Tag, pk=pk, owner=request.user)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, "Tag deleted.")
        return redirect('tag_list')
    return render(request, 'firstsite/tag_confirm_delete.html', {'tag': tag})

# SendNote functions
@login_required
def note_send_view(request, pk):
    """
    HTML flow:
    - GET: show a small form to enter recipient username
    - POST: validate, copy the note to recipient (including tags), log send event
    """
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == "POST":
        form = SendNoteForm(request.POST)
        if form.is_valid():

            username = form.cleaned_data['recipient_username'].strip()
            recipient = get_object_or_404(User, username=username)

            # Create a copy of the note for the recipient.
            copy = Note(
                title = note.title,
                content = note.content,
                owner =  recipient,
                is_pinned = False,
                is_archived = False,
            )
            # Copy tags if any
            attach_actor(copy, request.user)
            copy.save()
            copy.tags.set(note.tags.all())

            # Log send action
            NoteSend.objects.create(original_note=note, sender=request.user, recipient=recipient)
            log_note_event(request.user, note, NoteEvent.ACTION_SEND)

            messages.success(request, f"Note sent to {recipient.username}.")
            return redirect("note_detail", pk=note.pk)
    else:
        form = SendNoteForm()
    return render(request, "firstsite/send_note.html", {"form": form, "note": note})

@login_required
def inbox_list_view(request):
    """
    List notes received by the user via SendNote.
    """
    sends = NoteSend.objects.filter(recipient=request.user).select_related('original_note', 'sender')
    return render(request, 'firstsite/inbox_list.html', {'sends': sends})

@login_required
def sent_list_view(request):
    """
    List notes sent by the user via SendNote.
    """
    sends = NoteSend.objects.filter(sender=request.user).select_related('original_note', 'recipient')
    return render(request, 'firstsite/sent_list.html', {'sends': sends})

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
            note =  Note(owner =  request.user, **serializer.validated_data)
            attach_actor(note, request.user)
            note.save()
            
            #Attach tags (if any)
            tags = request.data.get('tags', [])
            if tags:
                note.tags.set(Tag.objects.filter(id__in=tags, owner=request.user))

            # Return the created note data
            return Response(NoteSerializer(note).data, status=201)
        # If the serializer is not valid, return the errors
        return Response(serializer.errors, status=400)

# API endpoint to retrieve a specific note
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_note_detail(request, pk):
    """
    Retrieve a specific note for the authenticated user.
    """
    
    note = get_object_or_404(Note, pk=pk, owner=request.user)

    # The NoteExists. Read a single note.
    if request.method == 'GET':
        # Retrieve the note details
        return Response(NoteSerializer(note).data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        # snapshot first for versioning
        NoteVersion.objects.create(
        note=note,
        title=note.title,
        content=note.content,
        updated_by=request.user
        )

        #  Update the note details
        serializer = NoteSerializer(note, data=request.data)
        if serializer.is_valid():
            attach_actor(note, request.user)
            serializer.save()
            #log_note_event(request.user, note, NoteEvent.ACTION_UPDATE)

            # update tags
            tags = request.data.get('tags', [])
            note.tags.set(Tag.objects.filter(id__in=tags, owner=request.user))
            
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        # Delete the note
        attach_actor(note, request.user)
        note.delete()
        
        # Same here as above, log delete event
        #log_note_event(request.user, None, NoteEvent.ACTION_DELETE)

        return Response(status=204)

# --- Analytics HTML page (server-rendered) ---
@login_required
def analytics_view(request):
    """
    Renders analytics using the same grouping logic as the API.
    Reads query params (?bucket= & actions=) for consistency.
    """
    # read choices from query params
    bucket = (request.GET.get('bucket') or 'daily').lower()
    

    actions = request.GET.getlist('actions') # multiple checkboxes functionality
    if not actions:
        actions = ['create', 'update', 'delete', 'send']

    allowed = {'create', 'update', 'delete', 'send'}
    actions = [a for a in actions if a in allowed] or ['create', 'update', 'delete', 'send']

    # Map bucket to trunc function
    trunc_map = {
        'daily': TruncDay('created_at'),
        'weekly': TruncWeek('created_at'),
        'monthly': TruncMonth('created_at'),
        'yearly': TruncYear('created_at'),
    }
    trunc = trunc_map.get(bucket, TruncDay('created_at'))
    if bucket not in trunc_map:
        bucket = 'daily'
    
    #aggregate NoteEvents
    qs = (NoteEvent.objects
        .filter(user=request.user, action__in=actions)
        .annotate(period=trunc)
        .values('period','action')
        .annotate(count=Count('id'))
        .order_by('period')
        )

    # assemble a consistent structure for rendering
    per_period = {}
    for row in qs:
        period_key = row['period'].date().isoformat()
        per_period.setdefault(period_key, {a: 0 for a in actions})
        per_period[period_key][row['action']] = row['count']

    periods = sorted(per_period.keys())  

    # build rows: [{period: "...", counts: {action: count}} ...]
    table_rows = []
    max_val = 1
    for period_key in periods:
        counts_for_period = []
        for a in actions:
            val = per_period[period_key].get(a, 0)
            counts_for_period.append(val)
            if val > max_val:
                max_val = val
        table_rows.append({
            'period': period_key,
            'counts': counts_for_period,  # aligned with actions
        })

    ctx = {
        'bucket': bucket,
        'actions': actions,
        'all_actions': ['create', 'update', 'delete', 'send'],
        'all_buckets': ['daily', 'weekly', 'monthly', 'yearly'],
        'table_rows': table_rows,
        'max_val': max_val,
        }   

    return render(request, 'firstsite/analytics.html', ctx)

# Note Version API endpoint
@api_view(['GET','DELETE','PUT'])
@permission_classes([IsAuthenticated])
def api_note_versions(request, pk):
    """
    Versions for a single note.

    GET    /api/notes/<pk>/versions/?page=1&page_size=20   -> paginated list (newest first)
    POST   /api/notes/<pk>/versions/                        -> create manual snapshot of current note
    DELETE /api/notes/<pk>/versions/?all=true               -> delete all versions (guarded)
    """
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    if request.method == 'GET':
        qs = note.versions.order_by('-timestamp')  # related_name='versions' on NoteVersion
        
        # Simple, explicit pagination
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get('page_size', 20))
        except ValueError:
            page_size = 20
        page_size = max(1, min(page_size, 100))  # cap at 10

        paginator = Paginator(qs, page_size)
        page_obj = paginator.get_page(page)
        data = NoteVersionSerializer(page_obj.object_list, many=True).data

        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'page': page_obj.number,
            'page_size': page_size,
            'results': data,
        }, status=status.HTTP_200_OK)

    if request.method == 'POST':
        v = NoteVersion.objects.create(
            note=note,
            title=note.title,
            content=note.content,
            updated_by=request.user,
        )
        return Response(NoteVersionSerializer(v).data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        # Guard (so a stray call can't wipe history)
        if request.GET.get('all') == 'true':
            note.versions.all().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Pass ?all=true to delete all versions.'},
                        status=status.HTTP_400_BAD_REQUEST)
# API restore version endpoint
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_note_restore_version(request, pk, version_id):
    """
    Restore a note from a specific version, snapshotting the current state first.
    POST /api/notes/<pk>/versions/<version_id>/restore/
    """
    note= get_object_or_404(Note, pk=pk, owner=request.user)
    version = get_object_or_404(NoteVersion, pk=version_id, note=note)

    # Snapshot the current state before restoring (so we don't lose it)
    NoteVersion.objects.create(
        note=note,
        title=note.title,
        content=note.content,
        updated_by=request.user,
    )

    # Restore the note's content from the selected version
    note.title = version.title
    note.content = version.content
    attach_actor(note, request.user)
    note.save(update_fields=['title', 'content', 'updated_at'])

    # Return the updated note data
    return Response(NoteSerializer(note).data, status=200)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_note_version_detail(request, pk, version_id):
    """
    Return a specific note version for a note the user owns.
    GET /api/notes/<pk>/versions/<version_id>/
    """
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    try:
        version = get_object_or_404(NoteVersion, pk = version_id, note= note)
        data = NoteVersionSerializer(version).data

        return Response(data, status=200)
    except NoteVersion.DoesNotExist:
        return Response({'error': 'Note version not found'}, status=404)

# API send note endpoint    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_note_send(request,pk):
    """
    POST /api/notes/<pk>/send/
    Body: {"recipient_username": "bob"}
    Action: creates a COPY for recipient; logs NoteSend + NoteEvent('send')
    """
    note = get_object_or_404(Note, pk=pk, owner=request.user)
    username = (request.data.get('recipient_username') or "").strip()
    # Validate recipient username
    if not username:
        return Response({'detail': 'Recipient username is required'}, status=400)
    
    try:
        recipient =  User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'detail': 'Recipient not found'}, status=404)

    # Create a copy of the note for the recipient.
    copy = Note(
        title = note.title,
        content = note.content,
        owner =  recipient,
        is_pinned = False,
        is_archived = False,
    )
    attach_actor(copy, request.user)  
    copy.save()
    # Copy tags if any
    copy.tags.set(note.tags.all())

    # Log send action
    NoteSend.objects.create(original_note=note, sender=request.user, recipient=recipient)
    log_note_event(request.user, note, NoteEvent.ACTION_SEND)
    
    # Return success response
    return Response({"status": "sent","recipient": recipient.username,"copy_id": copy.pk}, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_inbox_list(request):
    """
    List notes received by the user via NoteSend.
    GET /api/notes/inbox/
    """
    sends = NoteSend.objects.filter(recipient=request.user).select_related('original_note', 'sender')
    data = [
        {"id":s,id,
         "sender": s.sender.username if s.sender_id else None,
         "original_note_id": s.original_note_id,
         "created_at":s.created_at,
        } 
        for s in sends
    ]
    return Response(data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_sent_list(request):
    """
    List notes sent by the user via NoteSend.
    GET /api/notes/sent/
    """
    sends = NoteSend.objects.filter(sender=request.user).select_related('original_note', 'recipient')
    data = [
        {
            "id": s.id,
            "recipient": s.recipient.username if s.recipient_id else None,
            "original_note_id": s.original_note_id,
            "created_at": s.created_at,
        }
        for s in sends
        ]
    
    return Response(data, status=200)
# Note Analytics API endpoint
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_note_analytics(request):
    """
    Query params:
      - bucket: daily | weekly | monthly | yearly  (default: daily)
      - actions: comma-separated subset of: create,update,delete,send
                 (default: create,update,delete,send)
    Response:
      {
        "bucket": "daily",
        "actions": ["create","delete","send"],
        "series": {
          "2025-10-30": {"create": 2, "delete": 1, "send": 1},
          ...
        }
      }
    """
    # parse params 
    bucket =(request.GET.get('bucket') or 'daily').lower()
    raw_actions = (request.GET.get('actions') or 'create,update,delete,send').lower()
    actions = [a.strip() for a in raw_actions.split(',') if a.strip() ]

    # restrict actions, allowing certain values only
    allowed ={'create', 'update', 'delete', 'send'}
    actions = [a for a in actions if a in allowed]
    if not actions:
        actions = ['create','update','delete','send']
    
    #choose the trunc function
    trunc_map = {
        'daily': TruncDay('created_at'),
        'weekly': TruncWeek('created_at'),
        'monthly': TruncMonth('created_at'),
        'yearly': TruncYear('created_at'),
    }
    trunc = trunc_map.get(bucket, TruncDay('created_at'))
    if bucket not in trunc_map:
        bucket = 'daily'  # reset to default if invalid

    # aggregate
    qs = (NoteEvent.objects
        .filter(user=request.user, action__in=actions)
        .annotate(period=trunc)
        .values('period','action')
        .annotate(count=Count('id'))
        .order_by('period','action')
    )

    # Group data into {period: {action: count}}
    series = {}

    for row in qs:
        period = row['period']
        # I want to normalize period to ISO date string for JSON keys
        # (TruncWeek/Month/Year return datetimes too, safe to .date())
        key = period.date().isoformat() if hasattr(period, 'date') else str(period)
        series.setdefault(key, {})
        series[key][row['action']] = row['count']

    return Response({
        'bucket': bucket,
        'actions': actions,
        'series': series
    }, status=status.HTTP_200_OK)
# End of views.py

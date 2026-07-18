from math import ceil

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .utils import attach_actor, log_note_event
from .models import Note, NoteVersion, Tag, NoteSend, NoteEvent
from .serializers import NoteSerializer, TagSerializer, NoteVersionSerializer

"""
To generate tokens for users, you can use the following command in your terminal:
python manage.py drf_create_token 'your_username'
then use the generated token in your API requests as follows:
Authorization: Token your_generated_token

Have fun!
"""
# DRF API views. HTML (server-rendered) views live in views.py.

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
            # NoteEvent('update') is logged automatically by the post_save signal.
            # update tags
            tags = request.data.get('tags', [])
            note.tags.set(Tag.objects.filter(id__in=tags, owner=request.user))
            
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        # Delete the note
        attach_actor(note, request.user)
        note.delete()
        # NoteEvent('delete') is logged automatically by the post_delete signal.
        return Response(status=204)

# Note Version API endpoint
@api_view(['GET','POST','DELETE'])
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

# Helper function for pagination
def _paginate(request, qs, default_size=20, max_size=100):
    """
    Docstring for _paginate
    
    :param request: The HTTP request object containing query parameters for pagination.
    :param qs:  The Django QuerySet to be paginated.
    :param default_size: The default number of items per page if not specified in the request.
    :param max_size:  The maximum number of items allowed per page.
    :return: A tuple containing the list of items for the current page and a dictionary with pagination metadata.
    
    """
    try:
        page = max(int(request.GET.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        size = int(request.GET.get("page_size", default_size))
    except ValueError:
        size = default_size
    size = min(max(size, 1), max_size)

    total = qs.count()
    num_pages = ceil(total / size) if size else 1
    if page > num_pages and num_pages > 0:
        page = num_pages

    start = (page - 1) * size
    end = start + size
    items = list(qs[start:end])
    return items, {"count": total, "page": page, "page_size": size, "num_pages": num_pages}

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_inbox_list(request):
    """
    List notes received by the user via NoteSend.
    GET /api/notes/inbox/
    """
    qs = NoteSend.objects.filter(recipient=request.user).select_related("original_note", "sender").order_by("-created_at")
    items, meta = _paginate(request, qs)
    data = [
        {
            "id": s.id,
            "sender": s.sender.username if s.sender_id else None,
            "original_note_id": s.original_note_id,
            "created_at": s.created_at,
        }
        for s in items
    ]
    return Response({"results": data, **meta}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_sent_list(request):
    """
    List notes sent by the user via NoteSend.
    GET /api/notes/sent/
    """
    qs = NoteSend.objects.filter(sender=request.user).select_related("original_note", "recipient").order_by("-created_at")
    items, meta = _paginate(request, qs)
    data = [
        {
            "id": s.id,
            "recipient": s.recipient.username if s.recipient_id else None,
            "original_note_id": s.original_note_id,
            "created_at": s.created_at,
        }
        for s in items
    ]
    return Response({"results": data, **meta}, status=200)
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

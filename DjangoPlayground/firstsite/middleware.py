# We want to store request.user so singals can access it.
import threading
_local = threading.local()

def get_current_user():
    return getattr(_local, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware to attach the current user to thread local storage.
    This allows signals and other code to access the user making the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.user = getattr(request, 'user', None)
        try:
            return self.get_response(request)
        finally:
            _local.user = None  # Clean up after the request is done
        
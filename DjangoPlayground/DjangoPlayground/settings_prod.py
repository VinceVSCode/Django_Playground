from .settings_base import *

DEBUG = False

# On by default (a real deployment sits behind TLS). Set
# DJANGO_SECURE_SSL_REDIRECT=false to run this settings module locally over
# plain http (e.g. docker-compose.prod.yml without a TLS-terminating proxy) —
# the *_SECURE cookie flags ride the same switch since a browser silently
# drops "secure" cookies over http, which would otherwise break login.
_https = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "true").lower() == "true"
SECURE_SSL_REDIRECT = _https
SESSION_COOKIE_SECURE = _https
CSRF_COOKIE_SECURE = _https
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# Set ALLOWED_HOSTS via env in production, e.g. DJANGO_ALLOWED_HOSTS=yourdomain.com

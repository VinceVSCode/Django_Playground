from .settings_base import *

DEBUG = True

# Local development: no HTTPS hardening here (it lives in settings_prod and would
# break http://localhost — SECURE_SSL_REDIRECT / SESSION_COOKIE_SECURE require TLS).

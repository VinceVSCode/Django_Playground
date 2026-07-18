#!/bin/sh
# Apply migrations (creates the schema on the persistent volume on first run),
# then start the development server.
set -e

python manage.py migrate --noinput
exec python manage.py runserver 0.0.0.0:8000

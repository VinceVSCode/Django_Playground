#!/bin/sh
# Apply migrations (creates the schema on the persistent volume on first run),
# then start gunicorn. Static files were already collected at build time.
set -e

python manage.py migrate --noinput
exec gunicorn DjangoPlayground.wsgi:application --bind 0.0.0.0:8000

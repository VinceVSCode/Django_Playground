#!/usr/bin/env bash
set -e
export DJANGO_SETTINGS_MODULE=DjangoPlayground.settings_prod
# Set these in your shell/hosting env, not hardcoded here:
# export DJANGO_SECRET_KEY=... 
# export DJANGO_ALLOWED_HOSTS="yourdomain.com"
python manage.py collectstatic --noinput
# Example WSGI server (Linux):
gunicorn DjangoPlayground.wsgi:application --bind 0.0.0.0:8000

#!/usr/bin/env bash
set -e
export DJANGO_SETTINGS_MODULE=DjangoPlayground.settings_dev
python manage.py runserver

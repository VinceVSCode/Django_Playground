#!/bin/bash
# DjangoPlayground/firstsite/tests/ci_local_tests.sh
# This script runs the Django tests in a local CI-like environment.
# remember to give execute permissions: chmod +x ci_local_tests.sh
set -e
export DJANGO_SETTINGS_MODULE=DjangoPlayground.settings
echo "Upgrade pip "
python -m pip install --upgrade pip
echo "Install dependencies from requirements.txt if exists"
if [ -f requirements.txt ]; then
    python -m pip install -r requirements.txt
else
    echo "No requirements.txt found. Install Django manually."
    pip install django djangorestframework pytest pytest-django
fi
echo "Running Django tests..."
pytest --vv -rA --tb=short
echo "Tests completed."
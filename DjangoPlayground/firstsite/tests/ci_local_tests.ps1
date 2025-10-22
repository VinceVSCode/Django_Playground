#similar to ci_tests.sh but for local Windows PowerShell execution, no prints
$env:DJANGO_SETTINGS_MODULE = "DjangoPlayground.settings"
python -m pip install --upgrade pip
if (Test-Path requirements.txt) {
  pip install -r requirements.txt
} else {
  pip install django djangorestframework pytest pytest-django
}
pytest -vv -rA --tb=short

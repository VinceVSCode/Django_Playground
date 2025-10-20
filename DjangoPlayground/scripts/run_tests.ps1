$env:DJANGO_SETTINGS_MODULE = "DjangoPlayground.settings_dev"
pytest -vv -rA --tb=short

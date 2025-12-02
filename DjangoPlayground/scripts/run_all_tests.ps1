$ErrorActionPreference = "Stop"
$env:DJANGO_SETTINGS_MODULE = "DjangoPlayground.settings"

Write-Host "▶ Running analytics tests..."
pytest -q firstsite/tests/test_analytics.py

Write-Host "▶ Running UI smoke tests..."
pytest -q firstsite/tests/test_ui_smoke.py

# Add more as you grow:
# Write-Host "▶ Running send feature tests..."
# pytest -q firstsite/tests/test_send.py

Write-Host "[OK] All selected test suites passed."

$env:DJANGO_SETTINGS_MODULE = "DjangoPlayground.settings_dev"
pytest -q firstsite/tests/test_analytics.py
if ($LASTEXITCODE -eq 0) {
  Write-Host "[OK] Analytics feature tests passed."
} else {
  Write-Host "[FAIL] Analytics feature tests failed."
  exit 1
}

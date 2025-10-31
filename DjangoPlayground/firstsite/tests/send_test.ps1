$env:DJANGO_SETTINGS_MODULE = "DjangoPlayground.settings"
pytest -q firstsite/tests/test_send.py
if ($LASTEXITCODE -eq 0) {
  Write-Host "[OK] Send Note feature tests passed."
} else {
  Write-Host "[FAIL] Send Note feature tests failed."
  exit 1
}

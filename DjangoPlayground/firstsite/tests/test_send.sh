#!/usr/bin/env bash
set -e
export DJANGO_SETTINGS_MODULE=DjangoPlayground.settings
if pytest -q firstsite/tests/test_send.py; then
  echo "[OK] Send Note feature tests passed."
else
  echo "[FAIL] Send Note feature tests failed."
  exit 1
fi

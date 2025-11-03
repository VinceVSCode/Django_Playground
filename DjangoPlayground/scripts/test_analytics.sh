#!/usr/bin/env bash
set -e
export DJANGO_SETTINGS_MODULE=DjangoPlayground.settings
if pytest -q firstsite/tests/test_analytics.py; then
  echo "[OK] Analytics feature tests passed."
else
  echo "[FAIL] Analytics feature tests failed."
  exit 1
fi

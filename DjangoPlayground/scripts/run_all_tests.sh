#!/usr/bin/env bash
set -euo pipefail
export DJANGO_SETTINGS_MODULE=DjangoPlayground.settings

echo "▶ Running analytics tests..."
pytest -q firstsite/tests/test_analytics.py

echo "▶ Running UI smoke tests..."
pytest -q firstsite/tests/test_ui_smoke.py

# Add more as you grow:
# echo "▶ Running send feature tests..."
# pytest -q firstsite/tests/test_send.py

echo "[OK] All selected test suites passed."

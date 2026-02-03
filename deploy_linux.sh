#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "[1/7] Create venv..."
python3 -m venv .venv

echo "[2/7] Activate venv..."
source .venv/bin/activate

echo "[3/7] Install requirements..."
python -m pip install -r requirements.txt

echo "[4/7] Check daphne for ASGI..."
if ! python -m pip show daphne >/dev/null 2>&1; then
  echo "ERROR: daphne not installed. WebSocket will NOT work."
  echo "Run: python -m pip install daphne"
  exit 1
fi

echo "[5/7] Migrate database..."
python manage.py makemigrations game
python manage.py migrate

echo "[6/7] Create superuser if ADMIN_USER/ADMIN_PASS provided..."
if [ -n "$ADMIN_USER" ] && [ -n "$ADMIN_PASS" ]; then
  python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='$ADMIN_USER').exists() or User.objects.create_superuser('$ADMIN_USER','','$ADMIN_PASS')"
else
  echo "Skip: ADMIN_USER/ADMIN_PASS not set."
fi

echo "[7/7] Run dev server (ASGI)..."
python manage.py runserver 127.0.0.1:9001

#!/usr/bin/env bash
set -e

echo "[1/6] Create venv..."
python3 -m venv .venv

echo "[2/6] Activate venv..."
source .venv/bin/activate

echo "[3/6] Install requirements..."
pip install -r requirements.txt

echo "[4/6] Migrate database..."
python manage.py makemigrations game
python manage.py migrate

echo "[5/6] Create superuser if missing..."
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PASS=${ADMIN_PASS:-admin123}
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); User.objects.filter(username='$ADMIN_USER').exists() or User.objects.create_superuser('$ADMIN_USER','','$ADMIN_PASS')"

echo "[6/6] Run server..."
python manage.py runserver 0.0.0.0:9001

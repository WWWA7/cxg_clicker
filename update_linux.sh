#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

APP_NAME="cxg"

echo "[1/6] Activate venv..."
source .venv/bin/activate

echo "[2/6] Pull latest code (if git)..."
if [ -d .git ]; then
  git pull
else
  echo "Skip: not a git repo."
fi

echo "[3/6] Install/Update requirements..."
python -m pip install -r requirements.txt

echo "[4/6] Migrate database..."
python manage.py migrate

echo "[5/6] Collect static..."
python manage.py collectstatic --noinput

echo "[6/6] Cache bust static/game.js..."
STAMP=$(date +%Y%m%d%H%M)
sed -i "s#/static/js/game.js?v=[0-9]*#/static/js/game.js?v=${STAMP}#g" templates/base.html || true
if ! grep -q "/static/js/game.js?v=" templates/base.html; then
  sed -i "s#/static/js/game.js#/static/js/game.js?v=${STAMP}#g" templates/base.html
fi

echo "[7/7] Restart pm2..."
pm2 restart "$APP_NAME" --update-env

echo "Done."

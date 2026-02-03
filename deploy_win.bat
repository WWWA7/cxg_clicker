@echo off
setlocal
cd /d "%~dp0"

echo [1/7] Create venv...
python -m venv .venv

echo [2/7] Activate venv...
call .venv\Scripts\activate

echo [3/7] Install requirements...
python -m pip install -r requirements.txt

echo [4/7] Check daphne for ASGI...
python -m pip show daphne >nul 2>&1
if errorlevel 1 (
  echo ERROR: daphne not installed. WebSocket will NOT work.
  echo Run: python -m pip install daphne
  exit /b 1
)

echo [5/7] Migrate database...
python manage.py makemigrations game
python manage.py migrate

echo [6/7] Create superuser if ADMIN_USER/ADMIN_PASS provided...
if not "%ADMIN_USER%"=="" if not "%ADMIN_PASS%"=="" (
  python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); import os; u=os.getenv('ADMIN_USER'); p=os.getenv('ADMIN_PASS'); User.objects.filter(username=u).exists() or User.objects.create_superuser(u,'',p)"
) else (
  echo Skip: ADMIN_USER/ADMIN_PASS not set.
)

echo [7/7] Run dev server (ASGI)...
python manage.py runserver 127.0.0.1:9001

endlocal

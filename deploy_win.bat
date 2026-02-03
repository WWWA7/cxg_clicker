@echo off
setlocal
cd /d "%~dp0"

echo [1/6] Create venv...
python -m venv .venv

echo [2/6] Activate venv...
call .venv\Scripts\activate

echo [3/6] Install requirements...
python -m pip install -r requirements.txt

echo [4/6] Migrate database...
python manage.py makemigrations game
python manage.py migrate

echo [5/6] Create superuser if missing...
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); import os; u=os.getenv('ADMIN_USER','admin'); p=os.getenv('ADMIN_PASS','admin123'); User.objects.filter(username=u).exists() or User.objects.create_superuser(u,'',p)"

echo [6/6] Run server...
python manage.py runserver 0.0.0.0:9001

endlocal

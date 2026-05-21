@echo off
cd /d "%~dp0"
echo Simplify Jobs scraper — http://127.0.0.1:8000/
echo Jobright is a SEPARATE project: ..\Jobright_new (port 8001)
python manage.py runserver 8000 --noreload
pause

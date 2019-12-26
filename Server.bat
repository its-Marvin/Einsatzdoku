@echo off
rem Check for updates
rem git update
manage.py makemigrations doku
manage.py migrate

rem Check for first run
if not exist db.sqlite3 (
    echo Willkommen zur Einsatzdoku
    echo Vor dem ersten Start müssen ein paar Sachen konfiguriert werden.
    echo Enter zum fortsetzen
    pause
    manage.py makemigrations doku
    manage.py migrate
    echo Bitte einen Admin anlegen:
    manage.py createsuperuser
)

rem Server starten
venv\Scripts\python.exe server.py runserver 0.0.0.0:8000
pause
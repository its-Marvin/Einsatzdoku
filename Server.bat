@echo off
set first_run=False
if not exist db.sqlite3 (
    set first_run=True
)
rem Check if venv exists
if not exist venv\ (
    python -m pip install --user virtualenv
    python -m venv venv
    venv\Scripts\activate
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

rem Check for updates
git pull https://github.com/xJasonxy/Einsatzdoku.git master
venv\Scripts\python.exe manage.py makemigrations doku
venv\Scripts\python.exe manage.py migrate

rem Check for first run
if %first_run%==True (
    echo ###########################################################
    echo ##################  Einsatzdoku  ##########################
    echo ###########################################################
    echo Willkommen zur Ersteinrichtung.
    echo Vor dem ersten Start muss ein Adminaccount angelegt werden:
    venv\Scripts\python.exe manage.py createsuperuser
    echo ###########################################################
    echo #############  Einrichtung abgeschlossen!  ################
    echo #############    Server wird gestartet     ################
    echo ###########################################################
)

rem Server starten
venv\Scripts\python.exe server.py runserver 0.0.0.0:8000
pause
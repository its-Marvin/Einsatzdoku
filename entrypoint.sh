#!/bin/bash
python3 manage.py migrate doku
python3 manage.py migrate
daphne einsatzdoku.asgi:application -b 0.0.0.0
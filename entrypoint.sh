#!/usr/bin/env bash
set -euo pipefail

cd /app

if [[ ! -x /app/venv/bin/python || ! -x /app/venv/bin/daphne ]]; then
	echo "Virtual environment is missing required executables in /app/venv/bin" >&2
	exit 1
fi

/app/venv/bin/python manage.py migrate --noinput
exec /app/venv/bin/daphne einsatzdoku.asgi:application -b 0.0.0.0 -p 8000
#!/usr/bin/env bash
set -euo pipefail

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-gestion_ropa.settings}

mkdir -p /app/staticfiles
python manage.py migrate
python manage.py collectstatic --noinput
exec gunicorn gestion_ropa.wsgi:application --bind 0.0.0.0:${PORT:-8000} --log-level info --access-logfile -

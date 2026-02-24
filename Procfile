release: DJANGO_SETTINGS_MODULE=gestion_ropa.settings python manage.py migrate && DJANGO_SETTINGS_MODULE=gestion_ropa.settings python manage.py collectstatic --noinput
web: DJANGO_SETTINGS_MODULE=gestion_ropa.settings gunicorn gestion_ropa.wsgi:application

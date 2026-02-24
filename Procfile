release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn gestion_ropa.wsgi:application

from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = 'Verifica conectividad de settings_db ejecutando SELECT 1.'

    def handle(self, *args, **options):
        try:
            connection = connections['settings_db']
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                row = cursor.fetchone()
            self.stdout.write(self.style.SUCCESS(f'OK settings_db SELECT 1 => {row[0]}'))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'ERROR settings_db: {exc}'))
            raise SystemExit(1)

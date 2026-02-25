from django.core.management.base import BaseCommand

from apps.accounts.models import Organization
from apps.settings_app.models import EmailSettings, StoreSettings


class Command(BaseCommand):
    help = 'Verifica flujo rápido multi-DB para settings_app.'

    def handle(self, *args, **options):
        org = Organization.objects.using('default').create(name='Org MultiDB Check')
        store_settings, _ = StoreSettings.objects.using('settings_db').get_or_create(
            organization_id=org.id,
            defaults={'billing_legal_name': 'Org MultiDB Check SAS'},
        )
        email_settings, _ = EmailSettings.objects.using('settings_db').get_or_create(organization_id=org.id)
        email_settings.smtp_host = 'smtp.example.com'
        email_settings.smtp_from_email = 'noreply@example.com'
        email_settings.save(using='settings_db')

        store_settings.billing_city = 'Bogotá'
        store_settings.save(using='settings_db')

        self.stdout.write(self.style.SUCCESS(f'OK org(default)={org.id} settings(settings_db)={store_settings.organization_id}'))

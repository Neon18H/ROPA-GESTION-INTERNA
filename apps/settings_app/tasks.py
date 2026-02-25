import importlib.util
import smtplib

from apps.sales.models import Sale
from .models import EmailSettings

if importlib.util.find_spec('celery'):
    from celery import shared_task
else:
    def shared_task(func):
        return func


@shared_task
def send_smtp_test_email(org_id):
    email_settings = EmailSettings.objects.using('settings_db').get(organization_id=org_id)
    if not email_settings.smtp_host or not email_settings.smtp_from_email:
        return {'ok': False, 'error': 'SMTP no configurado'}

    with smtplib.SMTP(email_settings.smtp_host, email_settings.smtp_port, timeout=10) as server:
        if email_settings.smtp_use_tls:
            server.starttls()
        if email_settings.smtp_username:
            server.login(email_settings.smtp_username, email_settings.smtp_password)
        server.sendmail(
            email_settings.smtp_from_email,
            [email_settings.smtp_from_email],
            'Subject: SMTP test\n\nConfiguración SMTP válida.',
        )
    return {'ok': True}


@shared_task
def build_invoice_context(org_id, sale_id):
    email_settings = EmailSettings.objects.using('settings_db').get(organization_id=org_id)
    sale = Sale.objects.using('default').get(id=sale_id, organization_id=org_id)
    return {
        'sale_number': sale.number,
        'sale_total': str(sale.total),
        'smtp_from': email_settings.smtp_from_email,
    }

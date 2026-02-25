from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin

from .forms import BillingSettingsForm
from .models import EmailSettings, StoreSettings


class StoreSettingsView(LoginRequiredMixin, OrganizationRequiredMixin, TemplateView):
    template_name = 'settings_app/index.html'


class SettingsBillingView(LoginRequiredMixin, OrganizationRequiredMixin, TemplateView):
    template_name = 'settings_app/billing.html'

    def _get_org(self):
        return getattr(self.request, 'organization', None) or getattr(self.request.user, 'organization', None)

    def _get_settings(self):
        org = self._get_org()
        settings_obj, _ = StoreSettings.objects.using('settings_db').get_or_create(
            organization_id=org.id,
            defaults={
                'invoice_prefix': 'FAC',
                'next_invoice_number': 1,
                'currency': 'COP',
            },
        )
        email_settings, _ = EmailSettings.objects.using('settings_db').get_or_create(organization_id=org.id)
        return settings_obj, email_settings

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings_obj, email_settings = self._get_settings()
        context['form'] = kwargs.get('form') or BillingSettingsForm(instance=settings_obj, email_settings=email_settings)
        context['settings_obj'] = settings_obj
        return context

    def post(self, request, *args, **kwargs):
        settings_obj, email_settings = self._get_settings()
        form = BillingSettingsForm(request.POST, instance=settings_obj, email_settings=email_settings)
        if form.is_valid():
            try:
                with transaction.atomic(using='settings_db'):
                    form.save()
                    settings_obj.save(using='settings_db')
                messages.success(request, 'Configuración de facturación guardada correctamente.')
                return redirect('settings_app:settings_billing')
            except IntegrityError:
                form.add_error(None, 'No se pudo guardar la configuración por conflicto de datos. Intenta de nuevo.')
            except ValueError as exc:
                form.add_error('smtp_password', str(exc))

        messages.error(request, 'Revisa los campos marcados para continuar.')
        return self.render_to_response(self.get_context_data(form=form))

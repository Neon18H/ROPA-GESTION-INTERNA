from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin

from .forms import BillingSettingsForm
from .models import StoreSettings


class StoreSettingsView(LoginRequiredMixin, OrganizationRequiredMixin, TemplateView):
    template_name = 'settings_app/index.html'


class SettingsBillingView(LoginRequiredMixin, OrganizationRequiredMixin, TemplateView):
    template_name = 'settings_app/billing.html'

    def _get_settings(self):
        return StoreSettings.objects.get_or_create(organization=self.get_org())[0]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings_obj = self._get_settings()
        context['form'] = kwargs.get('form') or BillingSettingsForm(instance=settings_obj)
        context['settings_obj'] = settings_obj
        return context

    def post(self, request, *args, **kwargs):
        settings_obj = self._get_settings()
        form = BillingSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                messages.success(request, 'Configuración de facturación guardada correctamente.')
                return redirect('settings_app:settings_billing')
            except IntegrityError:
                form.add_error(None, 'No se pudo guardar la configuración por conflicto de datos. Intenta de nuevo.')

        messages.error(request, 'Revisa los campos marcados para continuar.')
        return self.render_to_response(self.get_context_data(form=form))

from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin


class StoreSettingsView(OrganizationRequiredMixin, TemplateView):
    template_name = 'settings_app/index.html'

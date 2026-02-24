from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin


class StoreSettingsView(LoginRequiredMixin, OrganizationRequiredMixin, TemplateView):
    template_name = 'settings_app/index.html'

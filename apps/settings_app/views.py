from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class StoreSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings_app/index.html'

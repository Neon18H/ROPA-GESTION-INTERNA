from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/index.html'

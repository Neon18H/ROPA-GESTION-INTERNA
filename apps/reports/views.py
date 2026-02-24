from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin


class ReportsView(LoginRequiredMixin, OrganizationRequiredMixin, TemplateView):
    template_name = 'reports/index.html'

from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin


class ReportsView(OrganizationRequiredMixin, TemplateView):
    template_name = 'reports/index.html'

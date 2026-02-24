from django.views.generic import TemplateView

from apps.common.mixins import RoleRequiredMixin


class ReportsView(RoleRequiredMixin, TemplateView):
    template_name = 'reports/index.html'
    allowed_roles = ('ADMIN', 'GERENTE')

from django.views.generic import TemplateView

from apps.common.mixins import RoleRequiredMixin
from apps.sales.models import Sale
from .models import Expense


class FinanceSummaryView(RoleRequiredMixin, TemplateView):
    template_name = 'finance/summary.html'
    allowed_roles = ('ADMIN', 'GERENTE')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.user.organization
        ingresos = Sale.objects.filter(organization=org).count()
        gastos = Expense.objects.filter(organization=org).count()
        ctx.update({'ingresos': ingresos, 'gastos': gastos})
        return ctx

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.sales.models import Sale
from .models import Expense


class FinanceSummaryView(LoginRequiredMixin, TemplateView):
    template_name = 'finance/summary.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.user.organization
        ingresos = Sale.objects.filter(organization=org).count()
        gastos = Expense.objects.filter(organization=org).count()
        ctx.update({'ingresos': ingresos, 'gastos': gastos})
        return ctx

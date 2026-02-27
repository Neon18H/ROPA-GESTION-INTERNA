import logging

from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView

from apps.common.mixins import RoleRequiredMixin
from apps.finance.services import build_purchase_csv, build_sales_csv, get_date_range, get_finance_data

logger = logging.getLogger(__name__)


class FinanceDashboardView(RoleRequiredMixin, TemplateView):
    template_name = 'finance/dashboard.html'
    allowed_roles = ('ADMIN', 'GERENTE')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'organization', None) or getattr(self.request.user, 'organization', None)
        range_key = self.request.GET.get('range', '30d')

        try:
            ctx.update(get_finance_data(org, range_key))
        except Exception:
            logger.exception('Finance dashboard render failed for organization_id=%s', getattr(org, 'id', None))
            ctx.update(
                {
                    'selected_range': '30d',
                    'cards': [],
                    'top_selling_products': [],
                    'unsold_products': [],
                    'top_purchased_products': [],
                    'top_suppliers': [],
                    'chart_payload': '{"incomeExpense":{"labels":[],"income":[],"expense":[]},"profitWeek":{"labels":[],"values":[]},"supplier":{"labels":[],"values":[]},"topSelling":{"labels":[],"values":[]}}',
                }
            )

        ctx['range_options'] = [('today', 'Hoy'), ('7d', '7 días'), ('30d', '30 días'), ('90d', '90 días')]
        return ctx


class FinanceSalesExportCSVView(RoleRequiredMixin, View):
    allowed_roles = ('ADMIN', 'GERENTE')

    def get(self, request, *args, **kwargs):
        org = getattr(request, 'organization', None) or getattr(request.user, 'organization', None)
        range_key = request.GET.get('range', '30d')
        _, start, end = get_date_range(range_key)
        csv_content = build_sales_csv(org, start, end)
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="ventas_{range_key}.csv"'
        return response


class FinancePurchasesExportCSVView(RoleRequiredMixin, View):
    allowed_roles = ('ADMIN', 'GERENTE')

    def get(self, request, *args, **kwargs):
        org = getattr(request, 'organization', None) or getattr(request.user, 'organization', None)
        range_key = request.GET.get('range', '30d')
        _, start, end = get_date_range(range_key)
        csv_content = build_purchase_csv(org, start, end)
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="compras_{range_key}.csv"'
        return response

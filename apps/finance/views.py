import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import DecimalField, Sum
from django.db.models.functions import Coalesce, TruncDate, TruncWeek
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.common.mixins import RoleRequiredMixin
from apps.finance.services import build_purchase_csv, build_sales_csv, get_date_range, get_finance_data
from apps.purchases.models import PurchaseOrder
from apps.sales.models import Sale

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

        now = timezone.localtime(timezone.now())
        tz = timezone.get_current_timezone()
        start14 = now - timedelta(days=13)
        start30 = now - timedelta(days=30)
        start8w = now - timedelta(weeks=8)
        dec_field = DecimalField(max_digits=12, decimal_places=2)

        if not org:
            ctx['finance_income_vs_expense_series'] = {'labels': [], 'income': [], 'expense': []}
            ctx['finance_weekly_profit_series'] = {'labels': [], 'profit': []}
            ctx['finance_expense_by_supplier_series'] = {'labels': [], 'totals': []}
            ctx['range_options'] = [('today', 'Hoy'), ('7d', '7 días'), ('30d', '30 días'), ('90d', '90 días')]
            return ctx

        sales_by_day_qs = (
            Sale.objects.filter(
                organization=org,
                created_at__date__gte=start14.date(),
                created_at__lte=now,
            )
            .annotate(day=TruncDate('created_at', tzinfo=tz))
            .values('day')
            .annotate(total=Coalesce(Sum('total'), Decimal('0.00'), output_field=dec_field))
            .order_by('day')
        )
        purchases_by_day_qs = (
            PurchaseOrder.objects.filter(
                organization=org,
                created_at__date__gte=start14.date(),
                created_at__lte=now,
            )
            .annotate(day=TruncDate('created_at', tzinfo=tz))
            .values('day')
            .annotate(total=Coalesce(Sum('total'), Decimal('0.00'), output_field=dec_field))
            .order_by('day')
        )

        sales_day_map = {row['day'].isoformat(): row['total'] for row in sales_by_day_qs}
        purchases_day_map = {row['day'].isoformat(): row['total'] for row in purchases_by_day_qs}

        income_expense_labels = []
        income_expense_income = []
        income_expense_expense = []
        for offset in range(14):
            current_date = (start14 + timedelta(days=offset)).date().isoformat()
            income_expense_labels.append(current_date)
            income_expense_income.append(float(sales_day_map.get(current_date, Decimal('0.00'))))
            income_expense_expense.append(float(purchases_day_map.get(current_date, Decimal('0.00'))))

        sales_by_week_qs = (
            Sale.objects.filter(
                organization=org,
                created_at__gte=start8w,
                created_at__lte=now,
            )
            .annotate(week=TruncWeek('created_at', tzinfo=tz))
            .values('week')
            .annotate(total=Coalesce(Sum('total'), Decimal('0.00'), output_field=dec_field))
            .order_by('week')
        )
        purchases_by_week_qs = (
            PurchaseOrder.objects.filter(
                organization=org,
                created_at__gte=start8w,
                created_at__lte=now,
            )
            .annotate(week=TruncWeek('created_at', tzinfo=tz))
            .values('week')
            .annotate(total=Coalesce(Sum('total'), Decimal('0.00'), output_field=dec_field))
            .order_by('week')
        )

        sales_week_map = {row['week'].date().isoformat(): row['total'] for row in sales_by_week_qs}
        purchases_week_map = {row['week'].date().isoformat(): row['total'] for row in purchases_by_week_qs}

        week_start = (start8w - timedelta(days=start8w.weekday())).date()
        weekly_labels = []
        weekly_profit = []
        for offset in range(8):
            week_date = week_start + timedelta(weeks=offset)
            week_key = week_date.isoformat()
            weekly_labels.append(week_key)
            income_value = sales_week_map.get(week_key, Decimal('0.00'))
            expense_value = purchases_week_map.get(week_key, Decimal('0.00'))
            weekly_profit.append(float(income_value - expense_value))

        expense_by_supplier_qs = (
            PurchaseOrder.objects.filter(
                organization=org,
                created_at__gte=start30,
                created_at__lte=now,
            )
            .values('supplier__name')
            .annotate(total=Coalesce(Sum('total'), Decimal('0.00'), output_field=dec_field))
            .order_by('-total')[:8]
        )

        supplier_labels = []
        supplier_totals = []
        for row in expense_by_supplier_qs:
            supplier_labels.append(row['supplier__name'] or 'Sin proveedor')
            supplier_totals.append(float(row['total']))

        ctx['finance_income_vs_expense_series'] = {
            'labels': income_expense_labels,
            'income': income_expense_income,
            'expense': income_expense_expense,
        }
        ctx['finance_weekly_profit_series'] = {'labels': weekly_labels, 'profit': weekly_profit}
        ctx['finance_expense_by_supplier_series'] = {'labels': supplier_labels, 'totals': supplier_totals}

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

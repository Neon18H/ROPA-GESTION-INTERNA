import json
from datetime import timedelta

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin
from apps.inventory.models import Stock
from apps.sales.models import Sale


DECIMAL_14_2 = DecimalField(max_digits=14, decimal_places=2)
ZERO_DEC = Value(0, output_field=DECIMAL_14_2)


class DashboardView(OrganizationRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.user.organization
        now = timezone.localtime()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)
        period_start = today_start - timedelta(days=29)

        sales_qs = Sale.objects.filter(organization=org, status=Sale.Status.PAID)
        sales_today = sales_qs.filter(created_at__gte=today_start)
        sales_month = sales_qs.filter(created_at__gte=month_start)

        inventory_cost_expr = Coalesce(
            F('avg_cost'),
            F('last_cost'),
            ZERO_DEC,
            output_field=DECIMAL_14_2,
        )
        inventory_value_expr = ExpressionWrapper(F('quantity') * inventory_cost_expr, output_field=DECIMAL_14_2)
        inventory_value = (
            Stock.objects.filter(variant__product__organization=org)
            .aggregate(
                total=Coalesce(
                    Sum(inventory_value_expr, output_field=DECIMAL_14_2),
                    ZERO_DEC,
                    output_field=DECIMAL_14_2,
                )
            )['total']
        )

        top_customers = list(
            sales_qs.values('customer_id', 'customer__name')
            .annotate(
                total_spent=Coalesce(
                    Sum('total', output_field=DECIMAL_14_2),
                    ZERO_DEC,
                    output_field=DECIMAL_14_2,
                ),
                orders=Count('id'),
            )
            .order_by('-total_spent')[:10]
        )

        daily_sales_rows = list(
            sales_qs.filter(created_at__gte=period_start)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(
                total=Coalesce(
                    Sum('total', output_field=DECIMAL_14_2),
                    ZERO_DEC,
                    output_field=DECIMAL_14_2,
                )
            )
            .order_by('day')
        )
        totals_by_day = {row['day']: row['total'] for row in daily_sales_rows}

        day_labels = []
        day_totals = []
        for offset in range(30):
            day = period_start.date() + timedelta(days=offset)
            day_labels.append(day.strftime('%Y-%m-%d'))
            day_totals.append(float(totals_by_day.get(day, 0)))

        customer_labels = [item['customer__name'] or 'Sin cliente' for item in top_customers]
        customer_totals = [float(item['total_spent']) for item in top_customers]

        sales_today_total = sales_today.aggregate(
            total=Coalesce(
                Sum('total', output_field=DECIMAL_14_2),
                ZERO_DEC,
                output_field=DECIMAL_14_2,
            )
        )['total']
        sales_month_total = sales_month.aggregate(
            total=Coalesce(
                Sum('total', output_field=DECIMAL_14_2),
                ZERO_DEC,
                output_field=DECIMAL_14_2,
            )
        )['total']

        ctx.update(
            {
                'sales_today_total': sales_today_total,
                'sales_month_total': sales_month_total,
                'sales_today_count': sales_today.count(),
                'low_stock_count': Stock.objects.filter(variant__product__organization=org, quantity__lte=F('min_alert')).count(),
                'inventory_value': inventory_value,
                'estimated_margin': sales_month_total - inventory_value if sales_month_total > inventory_value else 0,
                'top_customers': top_customers,
                'sales_line_data': json.dumps({'labels': day_labels, 'totals': day_totals}),
                'top_customers_chart_data': json.dumps({'labels': customer_labels, 'totals': customer_totals}),
            }
        )
        return ctx

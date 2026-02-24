from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin
from apps.inventory.models import Stock
from apps.sales.models import Sale, SaleItem


class DashboardView(OrganizationRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.user.organization
        now = timezone.localtime()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)

        sales_qs = Sale.objects.filter(organization=org, status=Sale.Status.PAID)
        sales_today = sales_qs.filter(created_at__gte=today_start)
        sales_month = sales_qs.filter(created_at__gte=month_start)

        top_products = (
            SaleItem.objects.filter(sale__organization=org, sale__status=Sale.Status.PAID)
            .values('variant__product__name')
            .annotate(qty=Coalesce(Sum('qty'), 0))
            .order_by('-qty', 'variant__product__name')[:5]
        )

        inventory_value_expr = ExpressionWrapper(F('quantity') * Coalesce(F('avg_cost'), F('last_cost')), output_field=DecimalField(max_digits=14, decimal_places=2))
        inventory_value = (
            Stock.objects.filter(variant__product__organization=org)
            .aggregate(total=Coalesce(Sum(inventory_value_expr), 0))['total']
        )

        low_stock_count = Stock.objects.filter(variant__product__organization=org, quantity__lte=F('min_alert')).count()

        ctx.update(
            {
                'sales_today_total': sales_today.aggregate(total=Coalesce(Sum('total'), 0))['total'],
                'sales_month_total': sales_month.aggregate(total=Coalesce(Sum('total'), 0))['total'],
                'sales_today_count': sales_today.count(),
                'low_stock_count': low_stock_count,
                'top_products': top_products,
                'inventory_value': inventory_value,
            }
        )
        return ctx

from datetime import timedelta
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from apps.common.mixins import RoleRequiredMixin
from apps.finance.models import Expense
from apps.inventory.models import Stock
from apps.purchases.models import PurchaseItem, PurchaseOrder
from apps.sales.models import Sale, SaleItem


DECIMAL_12_2 = DecimalField(max_digits=12, decimal_places=2)
ZERO_DEC = Value(Decimal('0.00'), output_field=DECIMAL_12_2)


class FinanceDashboardView(RoleRequiredMixin, TemplateView):
    template_name = 'finance/dashboard.html'
    allowed_roles = ('ADMIN', 'GERENTE')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.user.organization
        now = timezone.localtime()
        today = now.date()
        month_start = today.replace(day=1)
        start_30_days = today - timedelta(days=29)

        sales_base = Sale.objects.filter(organization=org, status=Sale.Status.PAID)
        month_sales = sales_base.filter(created_at__date__gte=month_start)

        ingresos_hoy = sales_base.filter(created_at__date=today).aggregate(
            total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
        )['total']
        ingresos_mes = month_sales.aggregate(
            total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
        )['total']

        gastos_operativos = Expense.objects.filter(
            organization=org,
            date__gte=month_start,
            date__lte=today,
        ).aggregate(total=Coalesce(Sum('amount', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))['total']

        purchase_month_total_expr = ExpressionWrapper(F('qty') * F('unit_cost'), output_field=DECIMAL_12_2)
        compras_mes = PurchaseItem.objects.filter(
            purchase__organization=org,
            purchase__status=PurchaseOrder.Status.RECEIVED,
            purchase__created_at__date__gte=month_start,
            purchase__created_at__date__lte=today,
        ).aggregate(
            total=Coalesce(Sum(purchase_month_total_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
        )['total']

        sale_cost_expr = ExpressionWrapper(
            F('qty') * Coalesce(F('variant__stock__avg_cost'), F('variant__stock__last_cost'), ZERO_DEC, output_field=DECIMAL_12_2),
            output_field=DECIMAL_12_2,
        )
        costo_estimado_mes = SaleItem.objects.filter(
            sale__organization=org,
            sale__status=Sale.Status.PAID,
            sale__created_at__date__gte=month_start,
            sale__created_at__date__lte=today,
        ).aggregate(
            total=Coalesce(Sum(sale_cost_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
        )['total']

        margen_estimado_mes = ingresos_mes - costo_estimado_mes - gastos_operativos

        inventory_value_expr = ExpressionWrapper(
            F('quantity') * Coalesce(F('avg_cost'), F('last_cost'), ZERO_DEC, output_field=DECIMAL_12_2),
            output_field=DECIMAL_12_2,
        )
        inventario_valorizado = Stock.objects.filter(variant__product__organization=org).aggregate(
            total=Coalesce(Sum(inventory_value_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
        )['total']

        revenue_expr = ExpressionWrapper(F('qty') * Coalesce(F('unit_price'), F('variant__price'), ZERO_DEC, output_field=DECIMAL_12_2), output_field=DECIMAL_12_2)
        top_productos = list(
            SaleItem.objects.filter(sale__organization=org, sale__status=Sale.Status.PAID)
            .values('variant__product__id', 'variant__product__name', 'variant__product__sku')
            .annotate(
                revenue=Coalesce(Sum(revenue_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2),
                total_qty=Coalesce(Sum('qty'), Value(0)),
            )
            .order_by('-revenue')[:10]
        )

        low_rotation_cutoff = timezone.now() - timedelta(days=30)
        sold_variant_ids = SaleItem.objects.filter(
            sale__organization=org,
            sale__status=Sale.Status.PAID,
            sale__created_at__gte=low_rotation_cutoff,
        ).values_list('variant_id', flat=True)
        baja_rotacion = list(
            Stock.objects.filter(variant__product__organization=org, quantity__gt=0)
            .exclude(variant_id__in=sold_variant_ids)
            .select_related('variant__product')
            .order_by('-quantity')[:10]
        )

        purchase_total_expr = ExpressionWrapper(F('qty') * F('unit_cost'), output_field=DECIMAL_12_2)
        compras_proveedor = list(
            PurchaseItem.objects.filter(
                purchase__organization=org,
                purchase__status=PurchaseOrder.Status.RECEIVED,
            )
            .values('purchase__supplier__name')
            .annotate(total=Coalesce(Sum(purchase_total_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
            .order_by('-total')[:10]
        )

        daily_sales = list(
            sales_base.filter(created_at__date__gte=start_30_days)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
            .order_by('day')
        )
        chart_sales_labels = [row['day'].isoformat() for row in daily_sales]
        chart_sales_values = [float(row['total']) for row in daily_sales]

        top_5 = top_productos[:5]
        chart_top_labels = [row['variant__product__name'] for row in top_5]
        chart_top_values = [float(row['revenue']) for row in top_5]

        expenses_by_category = list(
            Expense.objects.filter(organization=org, date__gte=month_start, date__lte=today)
            .values('category')
            .annotate(total=Coalesce(Sum('amount', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
            .order_by('-total')
        )
        chart_expense_labels = [row['category'] or 'Sin categoría' for row in expenses_by_category]
        chart_expense_values = [float(row['total']) for row in expenses_by_category]
        chart_expense_labels.extend(['Compras'])
        chart_expense_values.extend([float(compras_mes)])

        ctx.update(
            {
                'ingresos_hoy': ingresos_hoy,
                'ingresos_mes': ingresos_mes,
                'gastos_operativos_mes': gastos_operativos,
                'compras_mes': compras_mes,
                'margen_estimado_mes': margen_estimado_mes,
                'costo_estimado_mes': costo_estimado_mes,
                'inventario_valorizado': inventario_valorizado,
                'top_productos': top_productos,
                'baja_rotacion': baja_rotacion,
                'compras_proveedor': compras_proveedor,
                'chart_sales_labels': chart_sales_labels,
                'chart_sales_values': chart_sales_values,
                'chart_top_labels': chart_top_labels,
                'chart_top_values': chart_top_values,
                'chart_expense_labels': chart_expense_labels,
                'chart_expense_values': chart_expense_values,
            }
        )
        return ctx

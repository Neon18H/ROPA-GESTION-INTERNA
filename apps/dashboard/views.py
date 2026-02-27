import logging
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import DecimalField, IntegerField, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin
from apps.dashboard.services import get_dashboard_data
from apps.sales.models import Sale, SaleItem

logger = logging.getLogger(__name__)


class DashboardView(OrganizationRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request, 'organization', None) or getattr(self.request.user, 'organization', None)
        range_key = self.request.GET.get('range', '30d')

        try:
            ctx.update(get_dashboard_data(org, range_key))
        except Exception:
            logger.exception('Dashboard render failed for organization_id=%s', getattr(org, 'id', None))
            ctx.update(
                {
                    'selected_range': '30d',
                    'cards': [],
                    'top_products': [],
                    'top_customers': [],
                    'low_stock_products': [],
                    'top_customer_name': 'Sin datos',
                    'top_customer_total': 0,
                    'chart_payload': '{"incomeDaily":{"labels":[],"values":[]},"topProducts":{"labels":[],"values":[]},"brandSplit":{"labels":[],"values":[]}}',
                }
            )

        tz = timezone.get_current_timezone()
        now = timezone.localtime(timezone.now())
        start14 = now - timedelta(days=13)
        start30 = now - timedelta(days=30)

        daily_revenue_series = []
        top_sold_series = []
        sales_by_brand_series = []

        if org:
            daily_rows = (
                Sale.objects.filter(
                    organization=org,
                    status=Sale.Status.PAID,
                    created_at__gte=start14,
                    created_at__lte=now,
                )
                .annotate(day=TruncDate('created_at', tzinfo=tz))
                .values('day')
                .annotate(
                    total=Coalesce(
                        Sum('total'),
                        Value(0),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                )
                .order_by('day')
            )
            daily_revenue_series = [
                {'day': row['day'].isoformat(), 'total': float(row['total'])}
                for row in daily_rows
                if row.get('day')
            ]

            top_sold_rows = (
                SaleItem.objects.filter(
                    sale__organization=org,
                    sale__status=Sale.Status.PAID,
                    sale__created_at__gte=start30,
                    sale__created_at__lte=now,
                )
                .values('variant__product__sku', 'variant__product__name')
                .annotate(
                    total_qty=Coalesce(
                        Sum('qty'),
                        Value(0),
                        output_field=IntegerField(),
                    )
                )
                .order_by('-total_qty')[:5]
            )
            top_sold_series = [
                {
                    'label': (
                        f"{row['variant__product__sku']} - {row['variant__product__name']}"
                        if row.get('variant__product__sku')
                        else (row.get('variant__product__name') or 'Sin producto')
                    ),
                    'qty': int(row['total_qty'] or 0),
                }
                for row in top_sold_rows
            ]

            brand_rows = (
                SaleItem.objects.filter(
                    sale__organization=org,
                    sale__status=Sale.Status.PAID,
                    sale__created_at__gte=start30,
                    sale__created_at__lte=now,
                )
                .values('variant__product__brand__name')
                .annotate(
                    total=Coalesce(
                        Sum('line_total'),
                        Value(0),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                )
                .order_by('-total')[:8]
            )
            sales_by_brand_series = [
                {
                    'label': row.get('variant__product__brand__name') or 'Sin marca',
                    'total': float(row['total']),
                }
                for row in brand_rows
            ]

        ctx['daily_revenue_series'] = daily_revenue_series
        ctx['top_sold_series'] = top_sold_series
        ctx['sales_by_brand_series'] = sales_by_brand_series

        ctx['range_options'] = [
            ('today', 'Hoy'),
            ('7d', '7 días'),
            ('30d', '30 días'),
            ('90d', '90 días'),
        ]
        return ctx


class RoadmapView(LoginRequiredMixin, TemplateView):
    template_name = 'roadmap/index.html'
    login_url = 'accounts:login'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roadmap_items'] = [
            {
                'title': 'Testing del servicio de correos',
                'status': 'En progreso',
                'progress': 70,
            },
            {
                'title': 'Implementación de roles en el sistema',
                'status': 'En progreso',
                'progress': 40,
            },
            {
                'title': 'Mejoras en el dashboard principal',
                'status': 'Planificado',
                'progress': 15,
            },
        ]
        return ctx

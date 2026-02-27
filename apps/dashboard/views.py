import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin
from apps.dashboard.services import get_dashboard_data

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

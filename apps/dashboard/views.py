from django.views.generic import TemplateView

from apps.common.mixins import OrganizationRequiredMixin
from apps.inventory.models import Product, Stock
from apps.sales.models import Sale


class DashboardView(OrganizationRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.user.organization
        ventas_hoy = Sale.objects.filter(organization=org).count()
        ventas_mes = Sale.objects.filter(organization=org).count()
        inventario_valorizado = Stock.objects.filter(variant__product__organization=org).count()
        stock_bajo = Stock.objects.filter(variant__product__organization=org, quantity__lte=2).count()
        top_productos = Product.objects.filter(organization=org).order_by('name')[:5]
        ctx.update(
            {
                'ventas_hoy': ventas_hoy,
                'ventas_mes': ventas_mes,
                'inventario_valorizado': inventario_valorizado,
                'stock_bajo': stock_bajo,
                'top_productos': top_productos,
            }
        )
        return ctx

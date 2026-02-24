import csv
from io import TextIOWrapper

from django.contrib import messages
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from apps.common.mixins import OrganizationRequiredMixin, organization_required
from apps.common.models import OrganizationScopedMixin
from .forms import ProductForm
from .models import Brand, Category, Product, Stock, Variant


class ProductListView(OrganizationRequiredMixin, OrganizationScopedMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    paginate_by = 20


class ProductCreateView(OrganizationRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:products')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        messages.success(self.request, 'Producto creado')
        return super().form_valid(form)


@organization_required
def inventory_view(request):
    org = request.user.organization
    variants = Variant.objects.filter(product__organization=org).select_related('product', 'product__category', 'product__brand', 'stock')

    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    low_stock = request.GET.get('low_stock') == '1'

    if category_id:
        variants = variants.filter(product__category_id=category_id)
    if brand_id:
        variants = variants.filter(product__brand_id=brand_id)
    if low_stock:
        variants = variants.filter(stock__quantity__lte=models.F('stock__min_alert'))

    if request.method == 'POST':
        variant = get_object_or_404(Variant, id=request.POST.get('variant_id'), product__organization=org)
        stock, _ = Stock.objects.get_or_create(variant=variant)
        delta = int(request.POST.get('adjust_qty', 0))
        stock.quantity += delta
        stock.save(update_fields=['quantity'])
        messages.success(request, f'Ajuste aplicado a {variant.product.name} ({delta:+d}).')
        return redirect('inventory:inventory')

    context = {
        'variants': variants,
        'categories': Category.objects.filter(organization=org),
        'brands': Brand.objects.filter(organization=org),
        'low_stock_count': Stock.objects.filter(
            variant__product__organization=org, quantity__lte=models.F('min_alert')
        ).count(),
        'selected_category': category_id,
        'selected_brand': brand_id,
        'low_stock': low_stock,
    }
    return render(request, 'inventory/inventory.html', context)


@organization_required
def import_products(request):
    if request.method == 'POST' and request.FILES.get('file'):
        reader = csv.DictReader(TextIOWrapper(request.FILES['file'].file, encoding='utf-8'))
        for row in reader:
            Product.objects.get_or_create(
                organization=request.user.organization,
                sku=row['sku'],
                defaults={'name': row['name']},
            )
        messages.success(request, 'Importación completada')
        return redirect('inventory:products')
    return render(request, 'inventory/import.html')

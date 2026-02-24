from django.db import models
import csv
from io import TextIOWrapper
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from apps.common.models import OrganizationScopedMixin
from .models import Product, Variant, Stock
from .forms import ProductForm


class ProductListView(LoginRequiredMixin, OrganizationScopedMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    paginate_by = 20


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:products')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        messages.success(self.request, 'Producto creado')
        return super().form_valid(form)


def inventory_view(request):
    variants = Variant.objects.filter(product__organization=request.user.organization).select_related('product')
    low_stock = request.GET.get('low_stock') == '1'
    if low_stock:
        variants = variants.filter(stock__quantity__lte=models.F('stock__min_alert'))
    return render(request, 'inventory/inventory.html', {'variants': variants, 'low_stock_count': Stock.objects.filter(variant__product__organization=request.user.organization, quantity__lte=models.F('min_alert')).count()})


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

import csv
from io import TextIOWrapper

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db import transaction
from django.db.models import F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.common.mixins import RoleRequiredMixin, organization_required, role_required
from apps.common.models import OrganizationScopedMixin
from .forms import BrandForm, CategoryForm, ProductForm, StockMovementForm
from .models import Brand, Category, KardexEntry, Product, Stock, Variant
from .services import create_kardex_movement


class ProductListView(RoleRequiredMixin, OrganizationScopedMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        org = self.request.user.organization
        queryset = (
            Product.objects.filter(organization=org)
            .select_related('category', 'brand')
            .annotate(total_stock=Sum('variant__stock__quantity'))
            .order_by('name')
        )

        category_id = self.request.GET.get('category')
        brand_id = self.request.GET.get('brand')
        low_stock = self.request.GET.get('low_stock') == '1'

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
        if low_stock:
            queryset = queryset.filter(Q(total_stock__lte=3) | Q(total_stock__isnull=True))
        return queryset


class ProductCreateView(RoleRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:products')
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        org = self.request.user.organization
        initial_qty = form.cleaned_data.get('initial_qty') or 0
        initial_cost = form.cleaned_data.get('initial_cost') or 0

        with transaction.atomic():
            form.instance.organization = org
            self.object = form.save()

            default_variant = Variant.objects.create(
                product=self.object,
                size='UNICA',
                color='UNICO',
                gender=Variant.Gender.UNISEX,
                is_active=True,
            )
            Stock.objects.create(variant=default_variant, quantity=0)

            if initial_qty > 0:
                create_kardex_movement(
                    organization=org,
                    user=self.request.user,
                    variant=default_variant,
                    movement_type=KardexEntry.Type.IN,
                    qty=initial_qty,
                    unit_cost=initial_cost,
                    note='Stock inicial al crear producto',
                    reference=f'product-create:{self.object.id}',
                )

        messages.success(self.request, 'Producto creado')
        return redirect(self.get_success_url())


class ProductUpdateView(RoleRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:products')
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return Product.objects.filter(organization=self.request.user.organization)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs


@role_required('ADMIN', 'BODEGA')
def inventory_view(request):
    org = request.user.organization
    variants_without_stock = Variant.objects.filter(product__organization=org, stock__isnull=True).values_list('id', flat=True)
    Stock.objects.bulk_create([Stock(variant_id=variant_id, quantity=0) for variant_id in variants_without_stock], ignore_conflicts=True)

    variants = Variant.objects.filter(product__organization=org).select_related('product', 'product__category', 'product__brand', 'stock')

    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    low_stock = request.GET.get('low_stock') == '1'

    if category_id:
        variants = variants.filter(product__category_id=category_id)
    if brand_id:
        variants = variants.filter(product__brand_id=brand_id)
    if low_stock:
        variants = variants.filter(Q(stock__quantity__lte=F('stock__min_alert')) | Q(stock__quantity__isnull=True))

    if request.method == 'POST':
        form = StockMovementForm(request.POST, organization=org)
        if form.is_valid():
            qty = form.cleaned_data['qty']
            movement_type = form.cleaned_data['movement_type']
            if movement_type == KardexEntry.Type.ADJUST and request.POST.get('direction') == 'minus':
                qty = -qty
            create_kardex_movement(
                organization=org,
                user=request.user,
                variant=form.cleaned_data['variant'],
                movement_type=movement_type,
                qty=qty,
                unit_cost=form.cleaned_data.get('unit_cost') or 0,
                note=form.cleaned_data.get('note') or 'Ajuste manual desde inventario',
                reference='inventory-manual',
            )
            messages.success(request, 'Movimiento aplicado correctamente.')
            return redirect('inventory:inventory')

    context = {
        'variants': variants.order_by('product__name', 'size', 'color'),
        'categories': Category.objects.filter(organization=org),
        'brands': Brand.objects.filter(organization=org),
        'movement_form': StockMovementForm(organization=org),
        'low_stock_count': Stock.objects.filter(
            variant__product__organization=org, quantity__lte=models.F('min_alert')
        ).count(),
        'kardex_entries': KardexEntry.objects.filter(organization=org).select_related('variant__product').order_by('-created_at')[:10],
        'selected_category': category_id,
        'selected_brand': brand_id,
        'low_stock': low_stock,
    }
    return render(request, 'inventory/index.html', context)


@role_required('ADMIN', 'BODEGA')
def categories_view(request):
    org = request.user.organization
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.organization = org
            obj.save()
            messages.success(request, 'Categoría creada.')
            return redirect('inventory:categories')
    else:
        form = CategoryForm()
    return render(request, 'inventory/categories.html', {'items': Category.objects.filter(organization=org).order_by('name'), 'form': form})


@role_required('ADMIN', 'BODEGA')
def brands_view(request):
    org = request.user.organization
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.organization = org
            obj.save()
            messages.success(request, 'Marca creada.')
            return redirect('inventory:brands')
    else:
        form = BrandForm()
    return render(request, 'inventory/brands.html', {'items': Brand.objects.filter(organization=org).order_by('name'), 'form': form})


@role_required('ADMIN', 'BODEGA')
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


@login_required
@organization_required
def quick_create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.organization = request.user.organization
            obj.save()
            return JsonResponse({'ok': True, 'id': obj.id, 'name': obj.name})
    return JsonResponse({'ok': False}, status=400)


@login_required
@organization_required
def quick_create_brand(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.organization = request.user.organization
            obj.save()
            return JsonResponse({'ok': True, 'id': obj.id, 'name': obj.name})
    return JsonResponse({'ok': False}, status=400)

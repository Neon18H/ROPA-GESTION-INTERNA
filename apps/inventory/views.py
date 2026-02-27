import csv
import logging
from decimal import Decimal
from io import TextIOWrapper

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from apps.common.mixins import RoleRequiredMixin, organization_required, role_required
from apps.common.models import OrganizationScopedMixin
from .forms import (
    BrandForm,
    CategoryForm,
    ProductCreateForm,
    ProductUpdateForm,
    StockInForm,
    StockMovementForm,
    VariantInlineFormSet,
    VariantUpdateFormSet,
)
from .models import Brand, Category, KardexEntry, Product, Stock, Variant
from .services import create_kardex_movement


logger = logging.getLogger(__name__)


class ProductListView(RoleRequiredMixin, OrganizationScopedMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
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
    form_class = ProductCreateForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('inventory:products')
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_org()
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'variant_formset' not in ctx:
            initial = [{'size': 'UNICA', 'color': 'UNICO', 'gender': Variant.Gender.UNISEX}]
            ctx['variant_formset'] = VariantInlineFormSet(self.request.POST or None, self.request.FILES or None, prefix='variants', initial=initial)
        return ctx

    def form_valid(self, form):
        variant_formset = VariantInlineFormSet(self.request.POST, self.request.FILES, prefix='variants')
        if not variant_formset.is_valid():
            return self.form_invalid(form)

        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        initial_qty = form.cleaned_data.get('initial_qty') or 0
        initial_cost = form.cleaned_data.get('initial_cost') or Decimal('0')

        with transaction.atomic():
            form.instance.organization = org
            try:
                self.object = form.save()
            except ValidationError as exc:
                form.add_error(None, exc)
                return self.form_invalid(form)
            self._save_variants(self.object, variant_formset)

            default_variant = self.object.variant_set.order_by('id').first()
            if initial_qty > 0 and default_variant:
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

        self._safe_success_message('Producto creado')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form, variant_formset=VariantInlineFormSet(self.request.POST, self.request.FILES, prefix='variants'))
        )

    def _save_variants(self, product, variant_formset):
        created = 0
        for entry in variant_formset.cleaned_data:
            if not entry or entry.get('DELETE'):
                continue
            if not entry.get('size') and not entry.get('color') and not entry.get('barcode'):
                continue
            variant = Variant.objects.create(
                product=product,
                size=entry.get('size') or 'UNICA',
                color=entry.get('color') or 'UNICO',
                gender=entry.get('gender') or Variant.Gender.UNISEX,
                barcode=entry.get('barcode', ''),
                image=entry.get('image'),
                is_active=True,
            )
            Stock.objects.get_or_create(variant=variant, defaults={'quantity': 0})
            created += 1

        if created == 0:
            variant = Variant.objects.create(product=product, size='UNICA', color='UNICO', gender=Variant.Gender.UNISEX, is_active=True)
            Stock.objects.get_or_create(variant=variant, defaults={'quantity': 0})

    def _safe_success_message(self, message):
        try:
            messages.success(self.request, message)
        except Exception:
            logger.exception('No se pudo publicar mensaje de éxito en ProductCreateView.')


class ProductUpdateView(RoleRequiredMixin, UpdateView):
    model = Product
    form_class = ProductUpdateForm
    template_name = 'inventory/product_form.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return Product.objects.filter(organization=org)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_org()
        return kwargs

    def get_variant_formset(self):
        kwargs = {'instance': self.object, 'prefix': 'variants'}
        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return VariantUpdateFormSet(**kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['variant_formset'] = kwargs.get('variant_formset') or self.get_variant_formset()
        return ctx

    def get_success_url(self):
        try:
            return reverse('inventory:products')
        except Exception:
            logger.exception('No se pudo resolver inventory:products; fallback a inventory:inventory.')
            return '/inventory/'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        variant_formset = self.get_variant_formset()

        if not form.is_valid() or not variant_formset.is_valid():
            return self.form_invalid(form, variant_formset)

        return self.form_valid(form, variant_formset)

    def form_valid(self, form, variant_formset):
        form.instance.organization = self.get_org()

        try:
            with transaction.atomic():
                self.object = form.save()

                variants = variant_formset.save(commit=False)
                for deleted_variant in variant_formset.deleted_objects:
                    deleted_variant.is_active = False
                    deleted_variant.save(update_fields=['is_active'])

                for variant in variants:
                    variant.product = self.object
                    variant.size = (variant.size or 'UNICA').strip() or 'UNICA'
                    variant.color = (variant.color or 'UNICO').strip() or 'UNICO'
                    variant.gender = variant.gender or Variant.Gender.UNISEX
                    variant.save()
                    Stock.objects.get_or_create(variant=variant, defaults={'quantity': 0, 'min_alert': 0})

                variant_formset.save_m2m()

        except IntegrityError as exc:
            error_msg = str(exc)
            if 'uq_org_sku' in error_msg:
                form.add_error('sku', 'SKU ya existe')
            else:
                form.add_error(None, 'No se pudo actualizar el producto por una restricción de datos.')
            return self.form_invalid(form, variant_formset)
        except Exception:
            logger.exception('Error inesperado guardando ProductUpdateView.form_valid()')
            form.add_error(None, 'Ocurrió un error inesperado al guardar el producto.')
            return self.form_invalid(form, variant_formset)

        self._safe_success_message('Producto actualizado.')
        return redirect(self.get_success_url())

    def form_invalid(self, form, variant_formset=None):
        return self.render_to_response(self.get_context_data(form=form, variant_formset=variant_formset or self.get_variant_formset()))

    def _safe_success_message(self, message):
        try:
            messages.success(self.request, message)
        except Exception:
            logger.exception('No se pudo publicar mensaje de éxito en ProductUpdateView.')


class StockInView(RoleRequiredMixin, FormView):
    template_name = 'inventory/stock_in.html'
    form_class = StockInForm
    allowed_roles = ('ADMIN', 'BODEGA')

    def dispatch(self, request, *args, **kwargs):
        self.variant = get_object_or_404(Variant.objects.select_related('product'), pk=kwargs['variant_id'], product__organization=request.user.organization)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def get_initial(self):
        return {'variant': self.variant}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['variant'] = self.variant
        return ctx

    def form_valid(self, form):
        org = self.request.user.organization
        qty = form.cleaned_data['quantity']
        unit_cost = form.cleaned_data.get('unit_cost')

        with transaction.atomic():
            entry = KardexEntry.objects.create(
                organization=org,
                variant=form.cleaned_data['variant'],
                type=KardexEntry.Type.IN,
                qty=qty,
                unit_cost=unit_cost or 0,
                note=form.cleaned_data.get('note') or '',
                reference='inventory-stock-in',
                created_by=self.request.user,
            )

            stock, _ = Stock.objects.get_or_create(variant=entry.variant, defaults={'quantity': 0})
            previous_qty = stock.quantity
            stock.quantity = previous_qty + qty
            if unit_cost is not None:
                stock.last_cost = unit_cost
                total_prev = Decimal(previous_qty) * stock.avg_cost
                total_in = Decimal(qty) * unit_cost
                denominator = previous_qty + qty
                stock.avg_cost = ((total_prev + total_in) / Decimal(denominator)) if denominator > 0 else unit_cost
            stock.save(update_fields=['quantity', 'last_cost', 'avg_cost'])

        messages.success(self.request, 'Ingreso registrado correctamente.')
        return redirect('/inventory/')


class KardexInView(StockInView):
    pass


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

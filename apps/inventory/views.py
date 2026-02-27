import csv
import logging
from decimal import Decimal
from io import TextIOWrapper

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, ListView, UpdateView

from apps.common.mixins import RoleRequiredMixin, organization_required, role_required
from apps.common.models import OrganizationScopedMixin
from apps.purchases.models import PurchaseItem
from apps.sales.models import SaleItem
from apps.settings_app.models import StoreSettings
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
from .models import Brand, Category, KardexEntry, Product, ProductStock, Stock, Variant


logger = logging.getLogger(__name__)


def ensure_variant_stock_rows(product, initial_qty=None):
    qty = initial_qty if initial_qty is not None else 0
    for variant in product.variant_set.all():
        Stock.objects.get_or_create(variant=variant, defaults={'quantity': qty})


class ProductListView(RoleRequiredMixin, OrganizationScopedMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        queryset = (
            Product.objects.filter(organization=org, is_active=True)
            .select_related('category', 'brand')
            .annotate(total_stock=F('stock__qty'))
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


class ProductGalleryView(RoleRequiredMixin, ListView):
    model = Variant
    template_name = 'inventory/product_gallery.html'
    context_object_name = 'variants'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')

        queryset = (
            Variant.objects.filter(product__organization=org, product__is_active=True, is_active=True)
            .select_related('product', 'product__category', 'product__brand', 'product__stock')
            .order_by('product__name', 'id')
        )

        category_id = self.request.GET.get('category')
        brand_id = self.request.GET.get('brand')
        query = (self.request.GET.get('q') or '').strip()

        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        if brand_id:
            queryset = queryset.filter(product__brand_id=brand_id)
        if query:
            queryset = queryset.filter(
                Q(product__name__icontains=query)
                | Q(product__sku__icontains=query)
                | Q(size__icontains=query)
                | Q(color__icontains=query)
                | Q(gender__icontains=query)
                | Q(barcode__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_org()
        context.update(
            {
                'categories': Category.objects.filter(organization=org).order_by('name'),
                'brands': Brand.objects.filter(organization=org).order_by('name'),
                'selected_category': self.request.GET.get('category', ''),
                'selected_brand': self.request.GET.get('brand', ''),
                'q': (self.request.GET.get('q') or '').strip(),
                'default_min_alert': self._low_stock_default(),
            }
        )
        return context

    def _low_stock_default(self):
        org = self.get_org()
        if org is None:
            return 3
        return (
            StoreSettings.objects.filter(organization_id=org.id)
            .values_list('low_stock_default', flat=True)
            .first()
            or 3
        )


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
            # Variant uses product image; files are intentionally ignored on variant formset.
            ctx['variant_formset'] = VariantInlineFormSet(self.request.POST or None, prefix='variants', initial=initial)
        return ctx

    def form_valid(self, form):
        # Variant uses product image; files are intentionally ignored on variant formset.
        variant_formset = VariantInlineFormSet(self.request.POST, prefix='variants')
        if not variant_formset.is_valid():
            return self.form_invalid(form)

        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        initial_qty = form.cleaned_data.get('initial_qty') or 0
        initial_cost = form.cleaned_data.get('initial_cost') or Decimal('0')
        initial_sale_price = form.cleaned_data.get('initial_sale_price') or Decimal('0')

        with transaction.atomic():
            form.instance.organization = org
            form.instance.suggested_price = initial_sale_price
            try:
                self.object = form.save()
            except ValidationError as exc:
                form.add_error(None, exc)
                return self.form_invalid(form)
            self._save_variants(self.object, variant_formset, initial_sale_price=initial_sale_price)
            self._ensure_initial_stock(self.object, org, initial_qty=initial_qty, initial_cost=initial_cost)
            ensure_variant_stock_rows(self.object, initial_qty=initial_qty)

        self._safe_success_message('Producto creado')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form, variant_formset=VariantInlineFormSet(self.request.POST, prefix='variants'))
        )

    def _save_variants(self, product, variant_formset, initial_sale_price=Decimal('0')):
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
                is_active=True,
                default_sale_price=initial_sale_price,
                price=initial_sale_price,
            )
            created += 1

        if created == 0:
            variant = Variant.objects.create(
                product=product,
                size='UNICA',
                color='UNICO',
                gender=Variant.Gender.UNISEX,
                is_active=True,
                default_sale_price=initial_sale_price,
                price=initial_sale_price,
            )

    def _ensure_initial_stock(self, product, organization, initial_qty=0, initial_cost=Decimal('0')):
        stock, created = ProductStock.objects.get_or_create(
            organization=organization,
            product=product,
            defaults={
                'qty': initial_qty,
                'avg_cost': initial_cost,
                'last_cost': initial_cost,
            },
        )
        if not created:
            stock.qty = initial_qty
            stock.avg_cost = initial_cost
            stock.last_cost = initial_cost
            stock.save(update_fields=['qty', 'avg_cost', 'last_cost'])



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
        return Product.objects.filter(organization=org).prefetch_related('variant_set')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.get_org()
        return kwargs

    def get_variant_formset(self):
        kwargs = {'instance': self.object, 'prefix': 'variants'}
        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
        return VariantUpdateFormSet(**kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['variant_formset'] = kwargs.get('variant_formset') or self.get_variant_formset()
        ctx['variants'] = self.object.variant_set.order_by('id')
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
        form.instance.suggested_price = form.cleaned_data.get('initial_sale_price') or Decimal('0')

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
                    if variant.price in (None, 0):
                        variant.price = variant.default_sale_price or 0
                    variant.save()
                variant_formset.save_m2m()

                initial_sale_price = form.cleaned_data.get('initial_sale_price')
                if initial_sale_price is not None:
                    default_variant = self.object.variant_set.order_by('id').first()
                    if default_variant:
                        default_variant.default_sale_price = initial_sale_price
                        if default_variant.price in (None, 0):
                            default_variant.price = initial_sale_price
                        default_variant.save(update_fields=['default_sale_price', 'price'])

                ensure_variant_stock_rows(self.object, initial_qty=form.cleaned_data.get('initial_qty'))

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

            stock, _ = ProductStock.objects.get_or_create(
                organization=org,
                product=entry.variant.product,
                defaults={'qty': 0},
            )
            previous_qty = stock.qty
            stock.qty = previous_qty + qty
            if unit_cost is not None:
                stock.last_cost = unit_cost
                total_prev = Decimal(previous_qty) * stock.avg_cost
                total_in = Decimal(qty) * unit_cost
                denominator = previous_qty + qty
                stock.avg_cost = ((total_prev + total_in) / Decimal(denominator)) if denominator > 0 else unit_cost
            stock.save(update_fields=['qty', 'last_cost', 'avg_cost'])

        messages.success(self.request, 'Ingreso registrado correctamente.')
        return redirect('/inventory/')


class KardexInView(StockInView):
    pass


class ProductDeleteView(RoleRequiredMixin, View):
    allowed_roles = ('ADMIN', 'BODEGA')

    def post(self, request, pk, *args, **kwargs):
        organization = self.get_org()
        if organization is None:
            raise PermissionDenied('No organization associated to current user.')

        product = get_object_or_404(Product, pk=pk, organization=organization)

        has_links = self._has_links(product)
        if has_links:
            product.is_active = False
            product.save(update_fields=['is_active'])
            messages.info(request, 'El producto tiene movimientos relacionados. Se marcó como inactivo.')
            return redirect('inventory:products')

        if product.image:
            product.image.delete(save=False)
        product.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('inventory:products')

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['POST'])

    def _has_links(self, product):
        return (
            SaleItem.objects.filter(variant__product=product).exists()
            or PurchaseItem.objects.filter(variant__product=product).exists()
            or KardexEntry.objects.filter(variant__product=product).exists()
        )


@role_required('ADMIN', 'BODEGA')
def inventory_view(request):
    org = request.user.organization
    products_without_stock = Product.objects.filter(organization=org, stock__isnull=True).values_list('id', flat=True)
    ProductStock.objects.bulk_create(
        [ProductStock(product_id=product_id, organization=org, qty=0) for product_id in products_without_stock],
        ignore_conflicts=True,
    )

    variants = Variant.objects.filter(product__organization=org, product__is_active=True).select_related('product', 'product__category', 'product__brand', 'product__stock')

    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    low_stock = request.GET.get('low_stock') == '1'

    if category_id:
        variants = variants.filter(product__category_id=category_id)
    if brand_id:
        variants = variants.filter(product__brand_id=brand_id)
    if low_stock:
        variants = variants.filter(Q(product__stock__qty__lte=0) | Q(product__stock__isnull=True))

    context = {
        'variants': variants.order_by('product__name', 'size', 'color'),
        'categories': Category.objects.filter(organization=org),
        'brands': Brand.objects.filter(organization=org),
        'movement_form': StockMovementForm(organization=org),
        'low_stock_count': ProductStock.objects.filter(organization=org, qty__lte=0).count(),
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

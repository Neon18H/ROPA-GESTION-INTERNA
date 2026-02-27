from decimal import Decimal

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.audit.models import ActionLog
from apps.common.mixins import RoleRequiredMixin, role_required
from apps.inventory.models import Brand, Category, Product, Variant
from apps.settings_app.models import StoreSettings
from .forms import ManualVariantForm, PurchaseItemFormSet, PurchaseOrderForm, SupplierForm
from .models import PurchaseItem, PurchaseOrder, Supplier, SupplierVariant
from .services import receive_purchase


class PurchaseListView(RoleRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_list.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return PurchaseOrder.objects.filter(organization=self.request.user.organization).select_related('supplier')


@role_required('ADMIN', 'BODEGA')
def purchase_create_view(request):
    org = request.user.organization
    supplier_id = request.POST.get('supplier') if request.method == 'POST' else None
    show_all = request.POST.get('show_all_variants') == 'on'
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, organization=org)
        supplier_id = form.data.get('supplier')
        show_all = form.data.get('show_all_variants') == 'on'
        formset = PurchaseItemFormSet(
            request.POST,
            form_kwargs={'organization': org, 'supplier_id': supplier_id, 'show_all': show_all},
            prefix='items',
        )
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    next_number = (PurchaseOrder.objects.filter(organization=org).aggregate(m=Max('number'))['m'] or 0) + 1
                    purchase = form.save(commit=False)
                    purchase.organization = org
                    purchase.created_by = request.user
                    purchase.number = next_number
                    purchase.status = PurchaseOrder.Status.DRAFT
                    purchase.save()

                    subtotal = Decimal('0.00')
                    for item_form in formset:
                        if not item_form.cleaned_data or item_form.cleaned_data.get('DELETE'):
                            continue
                        qty = item_form.cleaned_data['qty']
                        unit_cost = item_form.cleaned_data['unit_cost']
                        variant = item_form.cleaned_data['variant']
                        line_total = Decimal(qty) * unit_cost
                        subtotal += line_total
                        PurchaseItem.objects.create(
                            purchase=purchase,
                            variant=variant,
                            qty=qty,
                            unit_cost=unit_cost,
                            line_total=line_total,
                        )

                        SupplierVariant.objects.update_or_create(
                            organization=org,
                            supplier=purchase.supplier,
                            variant=variant,
                            defaults={'last_purchase_cost': unit_cost, 'is_active': True},
                        )

                    purchase.subtotal = subtotal
                    purchase.total = subtotal
                    purchase.save(update_fields=['subtotal', 'total'])
                    receive_purchase(purchase, request.user)
            except IntegrityError:
                form.add_error(None, 'No se pudo guardar la orden. Verifique los datos e intente de nuevo.')
            else:
                messages.success(request, 'Orden de compra creada y recibida. Inventario actualizado.')
                return redirect('purchases:detail', pk=purchase.pk)
    else:
        form = PurchaseOrderForm(organization=org)
        formset = PurchaseItemFormSet(
            form_kwargs={'organization': org, 'supplier_id': supplier_id, 'show_all': show_all},
            prefix='items',
        )

    manual_variant_form = ManualVariantForm(request=request, organization=org)
    settings_obj = StoreSettings.objects.filter(organization_id=org.id).first()
    return render(
        request,
        'purchases/order_form.html',
        {
            'form': form,
            'formset': formset,
            'categories': Category.objects.filter(organization=org).order_by('name'),
            'brands': Brand.objects.filter(organization=org).order_by('name'),
            'sizes': (settings_obj.sizes if settings_obj else []),
            'colors': (settings_obj.colors if settings_obj else []),
            'gender_choices': Variant.Gender.choices,
            'manual_variant_form': manual_variant_form,
        },
    )


@require_POST
@role_required('ADMIN', 'BODEGA')
def purchase_create_manual_variant_ajax(request):
    org = request.user.organization
    form = ManualVariantForm(request.POST, request.FILES, request=request, organization=org)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    supplier = form.cleaned_data['supplier']
    if supplier.organization_id != org.id:
        return JsonResponse({'error': 'Proveedor inválido para esta organización.'}, status=400)

    try:
        with transaction.atomic():
            product, _ = Product.objects.get_or_create(
                organization=org,
                sku=form.cleaned_data['sku'],
                defaults={
                    'name': form.cleaned_data['product_name'],
                    'category': form.cleaned_data['category'],
                    'brand': form.cleaned_data['brand'],
                },
            )
            product.name = form.cleaned_data['product_name']
            if form.cleaned_data.get('category'):
                product.category = form.cleaned_data['category']
            if form.cleaned_data.get('brand'):
                product.brand = form.cleaned_data['brand']
            product.save(update_fields=['name', 'category', 'brand'])

            variant, _ = Variant.objects.get_or_create(
                product=product,
                size=form.cleaned_data.get('size') or '',
                color=form.cleaned_data.get('color') or '',
                gender=form.cleaned_data.get('gender') or Variant.Gender.UNISEX,
                barcode=form.cleaned_data.get('barcode') or '',
                defaults={'is_active': True, 'image': form.cleaned_data.get('image')},
            )
            if form.cleaned_data.get('image'):
                variant.image = form.cleaned_data['image']
                variant.save(update_fields=['image'])

            SupplierVariant.objects.update_or_create(
                organization=org,
                supplier=supplier,
                variant=variant,
                defaults={
                    'supplier_sku': form.cleaned_data['sku'],
                    'last_purchase_cost': form.cleaned_data['unit_cost'],
                    'is_active': True,
                },
            )
    except IntegrityError:
        return JsonResponse({'error': 'No se pudo crear la variante manual. Verifica SKU y datos únicos.'}, status=400)

    return JsonResponse(
        {
            'variant_id': variant.id,
            'variant_label': str(variant),
            'product_id': product.id,
            'qty': form.cleaned_data['qty'],
            'unit_cost': str(form.cleaned_data['unit_cost']),
        }
    )


class PurchaseDetailView(RoleRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return PurchaseOrder.objects.filter(organization=self.request.user.organization).select_related('supplier').prefetch_related('items__variant__product')


@require_POST
@role_required('ADMIN', 'BODEGA')
def purchase_receive_view(request, pk):
    purchase = get_object_or_404(
        PurchaseOrder.objects.filter(organization=request.user.organization).prefetch_related('items__variant'),
        pk=pk,
    )
    if purchase.status == PurchaseOrder.Status.RECEIVED:
        messages.info(request, 'La compra ya fue recibida anteriormente.')
        return redirect('purchases:detail', pk=pk)
    if purchase.status != PurchaseOrder.Status.DRAFT:
        messages.warning(request, 'Solo se pueden recibir compras en estado borrador.')
        return redirect('purchases:detail', pk=pk)

    receive_purchase(purchase, request.user)
    ActionLog.objects.create(
        organization=request.user.organization,
        user=request.user,
        action='RECEIVE_PURCHASE',
        model='PurchaseOrder',
        object_id=str(purchase.pk),
        metadata={'status': purchase.status},
    )
    messages.success(request, 'Compra recibida e inventario actualizado.')
    return redirect('purchases:detail', pk=pk)


class SupplierQuerysetMixin(RoleRequiredMixin):
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return Supplier.objects.filter(organization=self.request.user.organization).order_by('name')


class SupplierListView(SupplierQuerysetMixin, ListView):
    model = Supplier
    template_name = 'purchases/supplier_list.html'


class SupplierCreateView(SupplierQuerysetMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchases/supplier_form.html'
    success_url = reverse_lazy('purchases:suppliers')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        try:
            response = super().form_valid(form)
        except IntegrityError:
            form.add_error('name', 'Ya existe un proveedor con ese nombre en tu organización.')
            return self.form_invalid(form)
        messages.success(self.request, 'Proveedor creado correctamente.')
        return response


class SupplierUpdateView(SupplierQuerysetMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchases/supplier_form.html'
    success_url = reverse_lazy('purchases:suppliers')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except IntegrityError:
            form.add_error('name', 'Ya existe un proveedor con ese nombre en tu organización.')
            return self.form_invalid(form)
        messages.success(self.request, 'Proveedor actualizado correctamente.')
        return response


class SupplierDeleteView(SupplierQuerysetMixin, DeleteView):
    model = Supplier
    template_name = 'purchases/supplier_confirm_delete.html'
    success_url = reverse_lazy('purchases:suppliers')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Proveedor eliminado.')
        return super().delete(request, *args, **kwargs)

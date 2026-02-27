import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import F, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from apps.common.mixins import RoleRequiredMixin, role_required
from apps.customers.models import Customer
from apps.inventory.models import KardexEntry, ProductStock, Variant
from apps.settings_app.models import StoreSettings
from .forms import SaleForm, SaleItemFormSet
from .models import Payment, Sale, SaleItem
from .utils import D, compute_sale_totals

logger = logging.getLogger(__name__)


class SaleListView(RoleRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return Sale.objects.filter(organization=org).select_related('created_by', 'customer')


@role_required('ADMIN', 'VENDEDOR')
def pos_view(request):
    org = request.user.organization
    q = request.GET.get('q', '').strip()

    try:
        variants = Variant.objects.filter(product__organization=org, is_active=True).select_related('product', 'product__stock')
        if q:
            variants = variants.filter(Q(product__sku__icontains=q) | Q(barcode__icontains=q) | Q(product__name__icontains=q))

        if request.method == 'POST':
            form = SaleForm(request.POST, organization=org)
            formset = SaleItemFormSet(request.POST, prefix='items', form_kwargs={'organization': org})

            valid_items = []
            if formset.is_valid():
                for item_form in formset:
                    variant = item_form.cleaned_data.get('variant')
                    if not variant:
                        continue
                    qty = item_form.cleaned_data.get('quantity')
                    unit_price = item_form.cleaned_data.get('unit_price')
                    if not qty or unit_price is None:
                        continue
                    valid_items.append(
                        {
                            'variant': variant,
                            'qty': qty,
                            'unit_price': unit_price,
                            'tax_rate': item_form.cleaned_data.get('tax_rate'),
                            'discount': item_form.cleaned_data.get('discount') or D('0.00'),
                        }
                    )

            if not valid_items:
                messages.error(request, 'Debe seleccionar al menos un producto variante válido.')
            elif form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():
                        for item in valid_items:
                            stock = ProductStock.objects.select_for_update().filter(
                                organization=org,
                                product=item['variant'].product,
                            ).first()
                            current_stock = stock.qty if stock else 0
                            if item['qty'] > current_stock:
                                messages.error(request, f"Stock insuficiente para {item['variant'].product.name} {item['variant'].size}/{item['variant'].color}.")
                                transaction.set_rollback(True)
                                return redirect('sales:pos')

                        customer_mode = form.cleaned_data['customer_mode']
                        if customer_mode == SaleForm.CUSTOMER_MODE_NEW:
                            address = (form.cleaned_data.get('new_customer_address') or '').strip()
                            notes = f'Dirección: {address}' if address else ''
                            customer = Customer.objects.create(
                                organization=org,
                                name=form.cleaned_data['new_customer_name'].strip(),
                                phone=(form.cleaned_data.get('new_customer_phone') or '').strip(),
                                email=(form.cleaned_data.get('new_customer_email') or '').strip(),
                                document_id=(form.cleaned_data.get('new_customer_document') or '').strip(),
                                type=Customer.Type.NORMAL,
                                notes=notes,
                            )
                        else:
                            customer = form.cleaned_data['customer']
                            if customer.organization_id != org.id:
                                form.add_error('customer', 'Cliente inválido para esta organización.')
                                raise IntegrityError('Cross-organization customer selected.')

                        next_number = (Sale.objects.filter(organization=org).aggregate(m=Max('number'))['m'] or 0) + 1
                        sale = Sale.objects.create(
                            organization=org,
                            number=next_number,
                            customer=customer,
                            payment_method=form.cleaned_data['payment_method'],
                            created_by=request.user,
                            status=Sale.Status.PAID,
                        )

                        org_settings = StoreSettings.objects.using('settings_db').filter(organization_id=org.id).first()
                        default_vat_rate = org_settings.billing_vat_rate if org_settings else D('0.00')

                        class _ItemPayload:
                            def __init__(self, raw):
                                self.unit_price = raw['unit_price']
                                self.qty = raw['qty']
                                self.tax_rate = raw.get('tax_rate')

                        computed = compute_sale_totals([_ItemPayload(item) for item in valid_items], default_vat_rate)

                        discount_total = D('0.00')
                        for idx, item in enumerate(valid_items):
                            line = computed['lines'][idx]
                            line_total = line['line_total'] - item['discount']
                            discount_total += item['discount']
                            SaleItem.objects.create(
                                sale=sale,
                                variant=item['variant'],
                                qty=item['qty'],
                                unit_price=item['unit_price'],
                                tax_rate=item.get('tax_rate'),
                                discount=item['discount'],
                                line_total=line_total,
                            )
                            ProductStock.objects.filter(organization=org, product=item['variant'].product).update(qty=F('qty') - item['qty'])
                            KardexEntry.objects.create(
                                organization=org,
                                variant=item['variant'],
                                type=KardexEntry.Type.OUT,
                                qty=item['qty'],
                                unit_cost=0,
                                note='Venta',
                                reference=f'sale:{sale.id}',
                                created_by=request.user,
                            )

                        sale.subtotal = computed['subtotal']
                        sale.tax_total = computed['tax_total']
                        sale.discount_total = discount_total
                        sale.total = computed['total'] - discount_total
                        sale.save(update_fields=['subtotal', 'tax_total', 'discount_total', 'total'])
                        Payment.objects.create(sale=sale, method=sale.payment_method, amount=sale.total, reference='POS')
                except IntegrityError:
                    form.add_error(None, 'No fue posible registrar la venta por conflicto de datos. Revisa documento/email del cliente e intenta de nuevo.')
                else:
                    if form.cleaned_data['customer_mode'] == SaleForm.CUSTOMER_MODE_NEW:
                        messages.success(request, f'Cliente creado y venta #{sale.number} registrada.')
                    else:
                        messages.success(request, f'Venta #{sale.number} registrada.')
                    return redirect('sales:receipt', pk=sale.pk)
        else:
            form = SaleForm(organization=org)
            formset = SaleItemFormSet(prefix='items', form_kwargs={'organization': org})

        return render(request, 'sales/pos.html', {'form': form, 'items_formset': formset, 'variants': variants[:20], 'query': q})
    except Exception:
        logger.exception('pos_view failed for organization_id=%s', getattr(request.user, 'organization_id', None))
        raise


class SaleReceiptView(RoleRequiredMixin, DetailView):
    model = Sale
    template_name = 'sales/receipt.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return Sale.objects.filter(organization=org).select_related('customer').prefetch_related('items__variant__product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sale = context['object']
        org = self.get_org()
        billing_settings = StoreSettings.objects.using('settings_db').filter(organization_id=org.id).first()
        default_vat_rate = billing_settings.billing_vat_rate if billing_settings else D('0.00')
        computed = compute_sale_totals(sale.items.all(), default_vat_rate)
        context['billing_settings'] = billing_settings
        context['invoice'] = computed
        context['default_vat_rate'] = default_vat_rate
        return context


@role_required('ADMIN', 'VENDEDOR')
def sale_print_view(request, pk):
    sale = get_object_or_404(
        Sale.objects.filter(organization=request.user.organization).select_related('customer').prefetch_related('items__variant__product'),
        pk=pk,
    )
    billing_settings = StoreSettings.objects.using('settings_db').filter(organization_id=request.user.organization_id).first()
    default_vat_rate = billing_settings.billing_vat_rate if billing_settings else D('0.00')
    return render(
        request,
        'sales/receipt_print.html',
        {
            'sale': sale,
            'billing_settings': billing_settings,
            'invoice': compute_sale_totals(sale.items.all(), default_vat_rate),
            'default_vat_rate': default_vat_rate,
        },
    )

from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from apps.common.mixins import RoleRequiredMixin, role_required
from apps.customers.models import Customer
from apps.inventory.models import KardexEntry, Stock, Variant
from .forms import SaleForm, SaleItemFormSet
from .models import Payment, Sale, SaleItem


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
    variants = Variant.objects.filter(product__organization=org, is_active=True).select_related('product', 'stock')
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
                        'discount': item_form.cleaned_data.get('discount') or Decimal('0'),
                    }
                )

        if not valid_items:
            messages.error(request, 'Debe seleccionar al menos un producto variante válido.')
        elif form.is_valid() and formset.is_valid():
            with transaction.atomic():
                for item in valid_items:
                    stock = Stock.objects.select_for_update().filter(variant=item['variant']).first()
                    current_stock = stock.quantity if stock else 0
                    if item['qty'] > current_stock:
                        messages.error(request, f"Stock insuficiente para {item['variant'].product.name} {item['variant'].size}/{item['variant'].color}.")
                        transaction.set_rollback(True)
                        return redirect('sales:pos')

                customer = form.cleaned_data['customer']
                if not customer:
                    customer = Customer.objects.create(
                        organization=org,
                        name=form.cleaned_data['customer_name'],
                        phone=form.cleaned_data['customer_phone'],
                        email=form.cleaned_data['customer_email'],
                        document_id=form.cleaned_data['customer_document_id'],
                        type=form.cleaned_data.get('customer_type') or Customer.Type.NORMAL,
                        notes=form.cleaned_data['customer_notes'],
                    )

                next_number = (Sale.objects.filter(organization=org).aggregate(m=Max('number'))['m'] or 0) + 1
                sale = Sale.objects.create(
                    organization=org,
                    number=next_number,
                    customer=customer,
                    payment_method=form.cleaned_data['payment_method'],
                    created_by=request.user,
                    status=Sale.Status.PAID,
                )

                subtotal = Decimal('0')
                discount_total = Decimal('0')
                for item in valid_items:
                    line_total = (item['unit_price'] * item['qty']) - item['discount']
                    subtotal += item['unit_price'] * item['qty']
                    discount_total += item['discount']
                    SaleItem.objects.create(
                        sale=sale,
                        variant=item['variant'],
                        qty=item['qty'],
                        unit_price=item['unit_price'],
                        discount=item['discount'],
                        line_total=line_total,
                    )
                    Stock.objects.filter(variant=item['variant']).update(quantity=F('quantity') - item['qty'])
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

                sale.subtotal = subtotal
                sale.discount_total = discount_total
                sale.total = subtotal - discount_total
                sale.save(update_fields=['subtotal', 'discount_total', 'total'])
                Payment.objects.create(sale=sale, method=sale.payment_method, amount=sale.total, reference='POS')
            messages.success(request, f'Venta #{sale.number} registrada.')
            return redirect('sales:receipt', pk=sale.pk)
    else:
        form = SaleForm(organization=org)
        formset = SaleItemFormSet(prefix='items', form_kwargs={'organization': org})

    return render(request, 'sales/pos.html', {'form': form, 'items_formset': formset, 'variants': variants[:20], 'query': q})


class SaleReceiptView(RoleRequiredMixin, DetailView):
    model = Sale
    template_name = 'sales/receipt.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return Sale.objects.filter(organization=org).select_related('customer').prefetch_related('items__variant__product')


@role_required('ADMIN', 'VENDEDOR')
def sale_print_view(request, pk):
    sale = get_object_or_404(
        Sale.objects.filter(organization=request.user.organization).select_related('customer').prefetch_related('items__variant__product'),
        pk=pk,
    )
    return render(request, 'sales/receipt_print.html', {'sale': sale})

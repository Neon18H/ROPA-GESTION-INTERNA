from django import forms
from django.forms import formset_factory

from apps.customers.models import Customer
from apps.inventory.models import Variant
from .models import Sale


class SaleForm(forms.Form):
    CUSTOMER_MODE_EXISTING = 'existing'
    CUSTOMER_MODE_NEW = 'new'

    customer_mode = forms.ChoiceField(
        choices=[
            (CUSTOMER_MODE_EXISTING, 'Cliente existente'),
            (CUSTOMER_MODE_NEW, 'Cliente nuevo'),
        ],
        initial=CUSTOMER_MODE_EXISTING,
        widget=forms.RadioSelect,
        label='Tipo de cliente',
    )
    customer = forms.ModelChoiceField(queryset=Customer.objects.none(), required=False, label='Cliente existente')
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices, initial=Sale.PaymentMethod.CASH, label='Método de pago')

    new_customer_name = forms.CharField(required=False, label='Nombre completo')
    new_customer_document = forms.CharField(required=False, label='Documento')
    new_customer_phone = forms.CharField(required=False, label='Teléfono')
    new_customer_email = forms.EmailField(required=False, label='Email')
    new_customer_address = forms.CharField(required=False, label='Dirección')

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            self.fields['customer'].queryset = Customer.objects.filter(organization=organization).order_by('name')

        self.fields['customer'].widget.attrs.update({'class': 'form-select'})
        self.fields['payment_method'].widget.attrs.update({'class': 'form-select'})
        self.fields['customer_mode'].widget.attrs.update({'class': 'd-flex gap-3 list-unstyled mb-0'})

        for name in ('new_customer_name', 'new_customer_document', 'new_customer_phone', 'new_customer_email', 'new_customer_address'):
            self.fields[name].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('customer_mode') or self.CUSTOMER_MODE_EXISTING

        if mode == self.CUSTOMER_MODE_EXISTING:
            if not cleaned.get('customer'):
                self.add_error('customer', 'Debes seleccionar un cliente existente.')
            return cleaned

        if mode == self.CUSTOMER_MODE_NEW and not (cleaned.get('new_customer_name') or '').strip():
            self.add_error('new_customer_name', 'El nombre del cliente es obligatorio.')

        return cleaned


class SaleItemForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none(), required=False)
    quantity = forms.IntegerField(min_value=1, required=False)
    unit_price = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False)
    tax_rate = forms.DecimalField(min_value=0, max_value=100, decimal_places=2, max_digits=5, required=False)
    discount = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, initial=0)

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True)


SaleItemFormSet = formset_factory(SaleItemForm, extra=0)

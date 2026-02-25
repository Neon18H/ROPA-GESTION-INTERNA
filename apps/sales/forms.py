from django import forms
from django.forms import formset_factory

from apps.customers.models import Customer
from apps.inventory.models import Variant
from .models import Sale


class SaleForm(forms.Form):
    customer = forms.ModelChoiceField(queryset=Customer.objects.none(), required=False, label='Cliente existente')
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices, initial=Sale.PaymentMethod.CASH)

    customer_name = forms.CharField(required=False, label='Nombre cliente')
    customer_phone = forms.CharField(required=False, label='Teléfono')
    customer_email = forms.EmailField(required=False, label='Email')
    customer_document_id = forms.CharField(required=False, label='Documento')
    customer_type = forms.ChoiceField(required=False, choices=Customer.Type.choices)
    customer_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label='Notas')

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            self.fields['customer'].queryset = Customer.objects.filter(organization=organization).order_by('name')

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('customer') and not cleaned.get('customer_name'):
            self.add_error('customer_name', 'Debes seleccionar un cliente o crearlo en el flujo.')
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

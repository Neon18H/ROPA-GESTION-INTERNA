from decimal import Decimal

from django import forms

from .models import StoreSettings


class BillingSettingsForm(forms.ModelForm):
    class Meta:
        model = StoreSettings
        fields = [
            'billing_legal_name',
            'billing_tax_id',
            'billing_address',
            'billing_postal_code',
            'billing_email',
            'billing_phone',
            'billing_city',
            'billing_country',
            'billing_vat_rate',
        ]
        labels = {
            'billing_legal_name': 'Nombre legal',
            'billing_tax_id': 'NIT',
            'billing_address': 'Dirección',
            'billing_postal_code': 'Código postal',
            'billing_email': 'Correo facturación',
            'billing_phone': 'Teléfono',
            'billing_city': 'Ciudad',
            'billing_country': 'País',
            'billing_vat_rate': 'IVA (%)',
        }

        widgets = {
            'billing_legal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_address': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'billing_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_city': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_country': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }

    def clean_billing_vat_rate(self):
        vat_rate = self.cleaned_data.get('billing_vat_rate')
        if vat_rate is None:
            return Decimal('0.00')
        if vat_rate < Decimal('0.00') or vat_rate > Decimal('100.00'):
            raise forms.ValidationError('El IVA debe estar entre 0 y 100.')
        return vat_rate

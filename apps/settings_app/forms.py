from decimal import Decimal

from django import forms

from .models import EmailSettings, StoreSettings


class BillingSettingsForm(forms.ModelForm):
    smtp_host = forms.CharField(label='SMTP host', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    smtp_port = forms.IntegerField(label='SMTP puerto', min_value=1, max_value=65535, required=False, initial=587, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    smtp_username = forms.CharField(label='SMTP usuario', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    smtp_password = forms.CharField(label='SMTP password', required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}, render_value=False))
    smtp_use_tls = forms.BooleanField(label='Usar TLS', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    smtp_from_email = forms.EmailField(label='Email remitente', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = StoreSettings
        fields = [
            'invoice_prefix',
            'next_invoice_number',
            'currency',
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
            'invoice_prefix': 'Prefijo de factura',
            'next_invoice_number': 'Siguiente número de factura',
            'currency': 'Moneda',
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
            'invoice_prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'next_invoice_number': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
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

    def __init__(self, *args, email_settings=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_settings = email_settings
        if email_settings:
            self.fields['smtp_host'].initial = email_settings.smtp_host
            self.fields['smtp_port'].initial = email_settings.smtp_port
            self.fields['smtp_username'].initial = email_settings.smtp_username
            self.fields['smtp_use_tls'].initial = email_settings.smtp_use_tls
            self.fields['smtp_from_email'].initial = email_settings.smtp_from_email

    def clean_billing_vat_rate(self):
        vat_rate = self.cleaned_data.get('billing_vat_rate')
        if vat_rate is None:
            return Decimal('0.00')
        if vat_rate < Decimal('0.00') or vat_rate > Decimal('100.00'):
            raise forms.ValidationError('El IVA debe estar entre 0 y 100.')
        return vat_rate

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if self.email_settings is None:
            return instance

        self.email_settings.smtp_host = self.cleaned_data.get('smtp_host') or ''
        self.email_settings.smtp_port = self.cleaned_data.get('smtp_port') or 587
        self.email_settings.smtp_username = self.cleaned_data.get('smtp_username') or ''
        self.email_settings.smtp_use_tls = bool(self.cleaned_data.get('smtp_use_tls'))
        self.email_settings.smtp_from_email = self.cleaned_data.get('smtp_from_email') or ''

        smtp_password = self.cleaned_data.get('smtp_password')
        if smtp_password:
            self.email_settings.set_smtp_password(smtp_password)

        if commit:
            self.email_settings.save(using='settings_db')
        return instance

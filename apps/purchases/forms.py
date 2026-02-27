from django import forms
from django.forms import BaseFormSet, formset_factory

from apps.inventory.models import Brand, Category, Variant
from .models import PurchaseOrder, Supplier, SupplierVariant


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'email', 'address', 'notes', 'is_active']


class PurchaseOrderForm(forms.ModelForm):
    show_all_variants = forms.BooleanField(required=False, initial=False, label='Mostrar todas las variantes')

    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'notes']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.fields['supplier'].queryset = Supplier.objects.filter(organization=organization, is_active=True).order_by('name')


class PurchaseItemForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none())
    qty = forms.IntegerField(min_value=1)
    unit_cost = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def __init__(self, *args, organization=None, supplier_id=None, show_all=False, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Variant.objects.filter(product__organization=organization, is_active=True).select_related('product').order_by('product__name')
        if supplier_id and not show_all:
            supplier_variants = SupplierVariant.objects.filter(
                organization=organization,
                supplier_id=supplier_id,
                is_active=True,
            ).values_list('variant_id', flat=True)
            if supplier_variants:
                queryset = queryset.filter(id__in=supplier_variants)
        self.fields['variant'].queryset = queryset


class ManualVariantForm(forms.Form):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.none(), widget=forms.Select(attrs={'class': 'form-select'}))
    sku = forms.CharField(max_length=64)
    product_name = forms.CharField(max_length=180)
    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)
    brand = forms.ModelChoiceField(queryset=Brand.objects.none(), required=False)
    size = forms.CharField(max_length=16, required=False)
    color = forms.CharField(max_length=32, required=False)
    gender = forms.ChoiceField(choices=Variant.Gender.choices, required=False)
    barcode = forms.CharField(max_length=64, required=False)
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'capture': 'environment'}),
    )
    unit_cost = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    qty = forms.IntegerField(min_value=1)

    def __init__(self, *args, organization=None, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.organization = organization or getattr(getattr(request, 'user', None), 'organization', None)
        self.fields['supplier'].queryset = Supplier.objects.filter(organization=self.organization, is_active=True).order_by('name')
        self.fields['supplier'].widget.attrs.update({'id': 'manual_variant_supplier', 'class': 'form-select'})
        self.fields['category'].queryset = Category.objects.filter(organization=self.organization).order_by('name')
        self.fields['brand'].queryset = Brand.objects.filter(organization=self.organization).order_by('name')

        for field_name in ('sku', 'product_name', 'size', 'color', 'barcode', 'unit_cost', 'qty', 'image'):
            self.fields[field_name].widget.attrs.setdefault('class', 'form-control')
        for field_name in ('category', 'brand', 'gender'):
            self.fields[field_name].widget.attrs.setdefault('class', 'form-select')

    def clean_sku(self):
        return (self.cleaned_data.get('sku') or '').strip()

    def clean_product_name(self):
        return (self.cleaned_data.get('product_name') or '').strip()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            return image

        allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
        if getattr(image, 'content_type', '') not in allowed_types:
            raise forms.ValidationError('Formato no permitido. Usa JPG, PNG o WEBP.')
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError('La imagen no puede superar 5MB.')
        return image


class BasePurchaseItemFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        has_rows = False
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                has_rows = True
        if not has_rows:
            raise forms.ValidationError('Debe agregar al menos un ítem en la compra.')


PurchaseItemFormSet = formset_factory(PurchaseItemForm, formset=BasePurchaseItemFormSet, extra=1, can_delete=True)

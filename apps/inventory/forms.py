from django import forms
from django.forms import BaseInlineFormSet, formset_factory, inlineformset_factory

from .models import Brand, Category, KardexEntry, Product, Variant


class ProductCreateForm(forms.ModelForm):
    initial_qty = forms.IntegerField(min_value=0, required=False, label='Stock inicial', initial=0)
    initial_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, label='Costo inicial', help_text='Opcional para registrar Kardex de entrada inicial.')

    class Meta:
        model = Product
        fields = ['sku', 'name', 'category', 'brand', 'description', 'image', 'is_active', 'initial_qty', 'initial_cost']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.fields['category'].queryset = Category.objects.filter(organization=organization).order_by('name')
        self.fields['brand'].queryset = Brand.objects.filter(organization=organization).order_by('name')
        self.fields['category'].label_from_instance = lambda category: category.name
        self.fields['brand'].label_from_instance = lambda brand: brand.name
        self._apply_bootstrap_styles()

        if self.instance and self.instance.pk:
            self.fields['initial_qty'].required = False
            self.fields['initial_cost'].required = False
            self.fields['initial_qty'].disabled = True
            self.fields['initial_cost'].disabled = True
            self.fields['initial_qty'].help_text = 'Solo creación.'
            self.fields['initial_cost'].help_text = 'Solo creación.'

    def clean_sku(self):
        sku = (self.cleaned_data.get('sku') or '').strip()
        if not sku or not self.organization:
            return sku

        sku_exists = Product.objects.filter(organization=self.organization, sku=sku)
        if self.instance and self.instance.pk:
            sku_exists = sku_exists.exclude(pk=self.instance.pk)

        if sku_exists.exists():
            raise forms.ValidationError('Ya existe un producto con este SKU en la organización actual.')

        return sku

    def clean(self):
        cleaned_data = super().clean()
        initial_qty = cleaned_data.get('initial_qty') or 0
        initial_cost = cleaned_data.get('initial_cost')

        if initial_qty == 0:
            cleaned_data['initial_cost'] = initial_cost or 0
        return cleaned_data

    def clean_image(self):
        return validate_product_image(self.cleaned_data.get('image'))

    def _apply_bootstrap_styles(self):
        text_fields = ('sku', 'name', 'category', 'brand', 'description', 'initial_qty', 'initial_cost', 'image')
        for field_name in text_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.setdefault('class', 'form-control')
        self.fields['image'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
        self.fields['is_active'].widget.attrs.setdefault('class', 'form-check-input')


class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'category', 'brand', 'description', 'image', 'is_active']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.fields['category'].queryset = Category.objects.filter(organization=organization).order_by('name')
        self.fields['brand'].queryset = Brand.objects.filter(organization=organization).order_by('name')
        self.fields['category'].label_from_instance = lambda category: category.name
        self.fields['brand'].label_from_instance = lambda brand: brand.name
        text_fields = ('sku', 'name', 'category', 'brand', 'description', 'image')
        for field_name in text_fields:
            self.fields[field_name].widget.attrs.setdefault('class', 'form-control')
        self.fields['image'].widget.attrs.update({'class': 'form-control', 'accept': 'image/*'})
        self.fields['is_active'].widget.attrs.setdefault('class', 'form-check-input')

    def clean_sku(self):
        sku = (self.cleaned_data.get('sku') or '').strip()
        if not sku or not self.organization:
            return sku

        sku_exists = Product.objects.filter(organization=self.organization, sku=sku)
        if self.instance and self.instance.pk:
            sku_exists = sku_exists.exclude(pk=self.instance.pk)

        if sku_exists.exists():
            raise forms.ValidationError('Ya existe un producto con este SKU en la organización actual.')

        return sku

    def clean_image(self):
        return validate_product_image(self.cleaned_data.get('image'))


def validate_product_image(image):
    if not image:
        return image

    allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
    content_type = getattr(image, 'content_type', '')
    if content_type not in allowed_types:
        raise forms.ValidationError('Formato no permitido. Usa JPG, PNG o WEBP.')

    max_size_bytes = 5 * 1024 * 1024
    if image.size > max_size_bytes:
        raise forms.ValidationError('La imagen no puede superar 5MB.')

    return image


class BaseVariantUpdateInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        combinations = set()
        seen_barcodes = set()

        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            cleaned = form.cleaned_data
            if not cleaned or cleaned.get('DELETE'):
                continue

            size = (cleaned.get('size') or '').strip().upper() or 'UNICA'
            color = (cleaned.get('color') or '').strip().upper() or 'UNICO'
            gender = cleaned.get('gender') or Variant.Gender.UNISEX
            barcode = (cleaned.get('barcode') or '').strip()
            price = cleaned.get('price')

            key = (size, color, gender)
            if key in combinations:
                raise forms.ValidationError('No puedes repetir la misma combinación talla/color/género para este producto.')
            combinations.add(key)

            if barcode:
                normalized = barcode.upper()
                if normalized in seen_barcodes:
                    form.add_error('barcode', 'El código de barras está repetido en el formulario.')
                seen_barcodes.add(normalized)
                qs = Variant.objects.filter(product=self.instance, barcode__iexact=barcode)
                if form.instance.pk:
                    qs = qs.exclude(pk=form.instance.pk)
                if qs.exists():
                    form.add_error('barcode', 'Ya existe una variante de este producto con este código de barras.')

            if price is not None and price < 0:
                form.add_error('price', 'El precio no puede ser negativo.')


VariantUpdateFormSet = inlineformset_factory(
    Product,
    Variant,
    fields=['size', 'color', 'gender', 'barcode', 'is_active', 'price'],
    extra=1,
    can_delete=True,
    formset=BaseVariantUpdateInlineFormSet,
)


# Backward-compatible alias used by existing imports for creation flow.
ProductForm = ProductCreateForm


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['product', 'size', 'color', 'gender', 'barcode', 'is_active', 'price']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(organization=organization).order_by('name')


class VariantInlineForm(forms.Form):
    size = forms.CharField(max_length=16, required=False, initial='UNICA')
    color = forms.CharField(max_length=32, required=False, initial='UNICO')
    gender = forms.ChoiceField(required=False, choices=Variant.Gender.choices, initial=Variant.Gender.UNISEX)
    barcode = forms.CharField(max_length=64, required=False)

    def clean(self):
        cleaned = super().clean()
        if any(cleaned.get(field) for field in ('size', 'color', 'barcode')):
            cleaned['size'] = cleaned.get('size') or 'UNICA'
            cleaned['color'] = cleaned.get('color') or 'UNICO'
            cleaned['gender'] = cleaned.get('gender') or Variant.Gender.UNISEX
        return cleaned


VariantInlineFormSet = formset_factory(VariantInlineForm, extra=1, can_delete=True)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name']


class StockMovementForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none())
    qty = forms.IntegerField(min_value=1, label='Cantidad')
    unit_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, initial=0)
    note = forms.CharField(required=False)
    movement_type = forms.ChoiceField(choices=((KardexEntry.Type.IN, 'Ingreso inicial'), (KardexEntry.Type.ADJUST, 'Ajuste')))

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True)


class StockInForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none(), widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, label='Cantidad')
    unit_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, label='Costo unitario')
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label='Nota')

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True)

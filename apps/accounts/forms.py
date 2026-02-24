from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Organization

User = get_user_model()


class OrganizationRegistrationForm(forms.Form):
    store_name = forms.CharField(max_length=150, label='Nombre de la tienda')
    email = forms.EmailField(label='Correo electrónico')
    password1 = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este correo.')
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        if password1:
            validate_password(password1)
        return cleaned

    def save(self):
        store_name = self.cleaned_data['store_name'].strip()
        org = Organization.objects.create(name=store_name)
        email = self.cleaned_data['email'].lower()
        username = email.split('@')[0]
        base_username = username
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f'{base_username}{suffix}'
            suffix += 1
        user = User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data['password1'],
            organization=org,
            role=User.Role.ADMIN,
        )
        return org, user


class OrganizationUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password', 'is_active']

    def save(self, commit=True, organization=None):
        user = super().save(commit=False)
        user.organization = organization
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

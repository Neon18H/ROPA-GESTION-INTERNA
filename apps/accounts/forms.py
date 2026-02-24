from django import forms
from django.contrib.auth import get_user_model
from .models import Organization


User = get_user_model()


class OrganizationRegistrationForm(forms.Form):
    organization_name = forms.CharField(max_length=150)
    nit = forms.CharField(max_length=32, required=False)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def save(self):
        org = Organization.objects.create(name=self.cleaned_data['organization_name'], nit=self.cleaned_data['nit'])
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
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

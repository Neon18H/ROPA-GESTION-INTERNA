from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.views.generic import ListView, FormView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from apps.common.mixins import OrganizationRequiredMixin, organization_required
from .forms import OrganizationRegistrationForm, OrganizationUserForm

User = get_user_model()


class RegisterOrganizationView(FormView):
    template_name = 'accounts/register_org.html'
    form_class = OrganizationRegistrationForm
    success_url = reverse_lazy('dashboard:index')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.organization:
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        _, user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Tienda creada correctamente. ¡Bienvenido!')
        return super().form_valid(form)


class OrganizationUserListView(OrganizationRequiredMixin, ListView):
    template_name = 'accounts/user_list.html'
    model = User

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization)


@organization_required
def create_user(request):
    if request.method == 'POST':
        form = OrganizationUserForm(request.POST)
        if form.is_valid():
            form.save(organization=request.user.organization)
            messages.success(request, 'Usuario creado.')
            return redirect('accounts:user_list')
    else:
        form = OrganizationUserForm()
    return render(request, 'accounts/user_form.html', {'form': form})

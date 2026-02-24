from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from apps.common.mixins import RoleRequiredMixin, organization_required, role_required
from .forms import OrganizationRegistrationForm, OrganizationUserForm

User = get_user_model()


class RegisterOrganizationView(FormView):
    template_name = 'auth/register.html'
    form_class = OrganizationRegistrationForm
    success_url = reverse_lazy('dashboard:index')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, 'organization_id', None):
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        _, user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Tienda creada correctamente. ¡Bienvenido!')
        return super().form_valid(form)


class OrganizationUserListView(RoleRequiredMixin, ListView):
    template_name = 'accounts/user_list.html'
    model = User
    allowed_roles = (User.Role.ADMIN,)

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization).order_by('username')


@role_required(User.Role.ADMIN)
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


@role_required(User.Role.ADMIN)
def toggle_user_active(request, pk):
    user = get_object_or_404(User, pk=pk, organization=request.user.organization)
    if user.pk == request.user.pk:
        messages.warning(request, 'No puedes desactivar tu propio usuario.')
    else:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        messages.success(request, 'Estado de usuario actualizado.')
    return redirect('accounts:user_list')


@role_required(User.Role.ADMIN)
def reset_user_password(request, pk):
    user = get_object_or_404(User, pk=pk, organization=request.user.organization)
    temp_password = f"{user.username}1234"
    user.set_password(temp_password)
    user.save(update_fields=['password'])
    messages.success(request, f'Contraseña temporal para {user.username}: {temp_password}')
    return redirect('accounts:user_list')

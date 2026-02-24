from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, FormView
from .forms import OrganizationRegistrationForm, OrganizationUserForm
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterOrganizationView(FormView):
    template_name = 'accounts/register_org.html'
    form_class = OrganizationRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Tienda creada correctamente.')
        return super().form_valid(form)


class OrganizationUserListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/user_list.html'
    model = User

    def get_queryset(self):
        return User.objects.filter(organization=self.request.user.organization)


@login_required
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

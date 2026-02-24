from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class OrganizationRequiredMixin(LoginRequiredMixin):
    login_url = 'accounts:login'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.organization:
            messages.warning(request, 'Debes registrar una organización para continuar.')
            return redirect('accounts:register')
        return super().dispatch(request, *args, **kwargs)


def organization_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.organization:
            messages.warning(request, 'Debes registrar una organización para continuar.')
            return redirect('accounts:register')
        return view_func(request, *args, **kwargs)

    return _wrapped

from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class OrganizationRequiredMixin:
    def get_org(self):
        return getattr(self.request.user, 'organization', None) or getattr(self.request, 'organization', None)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not self.get_org():
            messages.warning(request, 'Debes registrar una organización para continuar.')
            return redirect('accounts:register')
        return super().dispatch(request, *args, **kwargs)


class OrganizationAccessMixin(LoginRequiredMixin, OrganizationRequiredMixin):
    login_url = 'accounts:login'


class RoleRequiredMixin(OrganizationAccessMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise PermissionDenied('No tienes permisos para acceder a este módulo.')
        return super().dispatch(request, *args, **kwargs)


def organization_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not getattr(request.user, 'organization_id', None):
            messages.warning(request, 'Debes registrar una organización para continuar.')
            return redirect('accounts:register')
        return view_func(request, *args, **kwargs)

    return _wrapped


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @organization_required
        def _wrapped(request, *args, **kwargs):
            if roles and request.user.role not in roles:
                raise PermissionDenied('No tienes permisos para acceder a este módulo.')
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator

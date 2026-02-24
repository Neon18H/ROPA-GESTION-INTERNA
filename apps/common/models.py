from django.db import models
from django.http import Http404


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrganizationScopedQuerySet(models.QuerySet):
    def for_user(self, user):
        if user.is_superuser and not user.organization_id:
            return self
        return self.filter(organization=user.organization)


class OrganizationScopedMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.for_user(self.request.user) if hasattr(qs, 'for_user') else qs.filter(organization=self.request.user.organization)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.request.user.is_superuser and not self.request.user.organization_id:
            return obj
        if hasattr(obj, 'organization_id') and obj.organization_id != self.request.user.organization_id:
            raise Http404('Objeto no disponible')
        return obj

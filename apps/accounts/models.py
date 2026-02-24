from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.common.models import OrganizationScopedQuerySet, TimestampedModel


class Organization(TimestampedModel):
    name = models.CharField(max_length=150)
    nit = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        GERENTE = 'GERENTE', 'Gerente'
        VENDEDOR = 'VENDEDOR', 'Vendedor'
        BODEGA = 'BODEGA', 'Bodega'

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VENDEDOR)


class OrganizationScopedModel(TimestampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    objects = OrganizationScopedQuerySet.as_manager()

    class Meta:
        abstract = True

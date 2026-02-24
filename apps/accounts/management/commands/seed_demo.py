from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization
from apps.inventory.models import Category, Brand, Product, Variant, Stock, KardexEntry


class Command(BaseCommand):
    help = 'Crea datos demo multi-tenant.'

    def handle(self, *args, **options):
        User = get_user_model()
        org, _ = Organization.objects.get_or_create(name='Demo Store', defaults={'nit': '900123'})
        for role in [User.Role.ADMIN, User.Role.GERENTE, User.Role.VENDEDOR, User.Role.BODEGA]:
            User.objects.get_or_create(username=role.lower(), defaults={'organization': org, 'role': role, 'email': f'{role.lower()}@demo.com'})
        cat, _ = Category.objects.get_or_create(organization=org, name='General')
        brand, _ = Brand.objects.get_or_create(organization=org, name='DemoBrand')
        admin = User.objects.filter(organization=org).first()
        for i in range(1, 11):
            p, _ = Product.objects.get_or_create(organization=org, sku=f'SKU-{i}', defaults={'name': f'Producto {i}', 'category': cat, 'brand': brand})
            v, _ = Variant.objects.get_or_create(product=p, size='M', color='Negro', gender='UNISEX')
            st, _ = Stock.objects.get_or_create(variant=v, defaults={'quantity': 20, 'min_alert': 5})
            KardexEntry.objects.get_or_create(organization=org, variant=v, type='IN', qty=st.quantity, unit_cost=50, created_by=admin)
        self.stdout.write(self.style.SUCCESS('Datos demo creados. Usuario sugerido: admin/admin1234'))

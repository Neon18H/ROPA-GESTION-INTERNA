# Gestión Interna Tienda de Ropa (Django 5)

Proyecto multi-tenant por organización para gestión interna de tiendas de ropa.

## Características clave
- Multi-tenant por `Organization` y `User.organization`.
- Roles: `ADMIN`, `GERENTE`, `VENDEDOR`, `BODEGA`.
- Módulos: inventario, ventas, clientes, compras, finanzas, promociones, devoluciones, reportes, settings.
- Dashboard con KPIs y layout Bootstrap 5 estilo admin.
- PostgreSQL only (sin SQLite).
- Deploy listo para Railway.

## Variables de entorno (Railway)
- `DATABASE_URL`
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS=ropa-gestion-interna-production.up.railway.app`
- `CSRF_TRUSTED_ORIGINS=https://ropa-gestion-interna-production.up.railway.app`

## Comandos
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py seed_demo
```

## Credenciales demo local
- Usuario sugerido: `admin`
- Password sugerido: `admin1234`

> Cambia credenciales en ambientes reales.

## URLs principales
- `/` dashboard
- `/inventory/`
- `/sales/`
- `/customers/`
- `/purchases/`
- `/finance/`
- `/reports/`
- `/promotions/`
- `/returns/`
- `/settings/`

## Deploy Railway
1. Conecta repo en Railway.
2. Define variables de entorno.
3. Deploy command: `python manage.py migrate && python manage.py collectstatic --noinput`.
4. Start command: `gunicorn gestion_ropa.wsgi:application`.

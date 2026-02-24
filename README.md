# Gestión Interna Tienda de Ropa (Django 5)

Proyecto multi-tenant por organización para gestión interna de tiendas de ropa.

## Características clave
- Multi-tenant por `Organization` y `User.organization`.
- Roles: `ADMIN`, `GERENTE`, `VENDEDOR`, `BODEGA`.
- Módulos: inventario, ventas, clientes, compras, finanzas, promociones, devoluciones, reportes, settings.
- UI SaaS Enterprise responsive con Bootstrap 5.3.3, Bootstrap Icons e Inter.
- PostgreSQL only (sin SQLite).
- Deploy listo para Railway con arranque idempotente.

## Variables de entorno (Railway)
- `DATABASE_URL`
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS=ropa-gestion-interna-production.up.railway.app`
- `CSRF_TRUSTED_ORIGINS=https://ropa-gestion-interna-production.up.railway.app`
- `DJANGO_SETTINGS_MODULE=gestion_ropa.settings`
- `WHITENOISE_USE_FINDERS=False` (fallback opcional, activar solo si Railway no ejecuta `collectstatic`)

## Arranque en Railway (fix definitivo de estáticos)
El proceso `web` usa `start.sh` y ejecuta siempre:

1. `mkdir -p /app/staticfiles`
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput`
4. `gunicorn gestion_ropa.wsgi:application --bind 0.0.0.0:$PORT --log-level info --access-logfile -`

`Procfile`:

```procfile
release: DJANGO_SETTINGS_MODULE=gestion_ropa.settings python manage.py migrate && DJANGO_SETTINGS_MODULE=gestion_ropa.settings python manage.py collectstatic --noinput
web: bash start.sh
```

## Comandos locales
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py seed_demo
```

## Verificación de estáticos en producción
Con la app desplegada, validar headers reales:

```bash
curl -I https://<tu-dominio>/static/css/theme.css
curl -I https://<tu-dominio>/static/js/app.js
```

Resultados esperados:
- `/static/css/theme.css` -> `HTTP/1.1 200 OK` y `Content-Type: text/css`
- `/static/js/app.js` -> `HTTP/1.1 200 OK` y `Content-Type: application/javascript`

Si responde `text/html` o `404`, el proceso web no está ejecutando `collectstatic` o está usando otra imagen/instancia.

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

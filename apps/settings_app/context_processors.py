from django.db import OperationalError, ProgrammingError
from apps.settings_app.models import StoreSettings


def store_settings(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'store_settings': None}

    cached = getattr(request, '_cached_store_settings', None)
    if cached is not None:
        return {'store_settings': cached}

    organization = getattr(request, 'organization', None) or getattr(request.user, 'organization', None)
    if organization is None:
        request._cached_store_settings = None
        return {'store_settings': None}

    try:
        settings = StoreSettings.objects.using('settings_db').filter(organization_id=organization.id).first()
    except (OperationalError, ProgrammingError):
        settings = None
    request._cached_store_settings = settings
    return {'store_settings': settings}

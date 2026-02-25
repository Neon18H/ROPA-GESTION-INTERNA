from django.db import OperationalError, ProgrammingError
from django import template

from apps.common.money import convert_cop_to_usd, money_cop as format_money_cop, money_usd as format_money_usd
from apps.common.request_context import get_current_request
from apps.settings_app.models import StoreSettings

register = template.Library()


def _get_store_settings(request):
    if request is None:
        return None
    cached = getattr(request, '_cached_store_settings', None)
    if cached is not None:
        return cached
    organization = getattr(request, 'organization', None) or getattr(getattr(request, 'user', None), 'organization', None)
    if organization is None:
        return None
    try:
        settings = StoreSettings.objects.using('settings_db').filter(organization_id=organization.id).first()
    except (OperationalError, ProgrammingError):
        settings = None
    request._cached_store_settings = settings
    return settings


@register.filter(name='money')
def money(amount):
    request = get_current_request()
    settings = _get_store_settings(request)
    rounding_policy = settings.rounding_policy if settings else 'HALF_UP'
    cop_text = format_money_cop(amount, rounding_policy=rounding_policy)
    if not settings or not settings.show_dual_currency:
        return cop_text
    usd_amount = convert_cop_to_usd(amount, settings.fx_usd_cop_rate, rounding_policy=rounding_policy)
    usd_text = format_money_usd(usd_amount, rounding_policy=rounding_policy) if usd_amount is not None else '—'
    return f'{cop_text} ({usd_text})'


@register.filter(name='money_cop')
def money_cop_filter(amount):
    return format_money_cop(amount)


@register.filter(name='money_usd')
def money_usd_filter(amount, fx_rate):
    usd_amount = convert_cop_to_usd(amount, fx_rate)
    return format_money_usd(usd_amount) if usd_amount is not None else '—'

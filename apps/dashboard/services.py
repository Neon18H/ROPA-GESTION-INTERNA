import json
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Count, DecimalField, ExpressionWrapper, F, IntegerField, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.customers.models import Customer
from apps.inventory.models import Product, Stock
from apps.purchases.models import PurchaseItem, PurchaseOrder
from apps.sales.models import Sale, SaleItem
from apps.settings_app.models import StoreSettings

DECIMAL_12_2 = DecimalField(max_digits=12, decimal_places=2)
INT_FIELD = IntegerField()
ZERO_DEC = Value(Decimal('0.00'), output_field=DECIMAL_12_2)
ZERO_INT = Value(0, output_field=INT_FIELD)
RANGE_DAYS = {
    'today': 1,
    '7d': 7,
    '30d': 30,
    '90d': 90,
}


def get_date_range(range_key):
    key = range_key if range_key in RANGE_DAYS else '30d'
    now = timezone.localtime(timezone.now())
    end = now
    days = RANGE_DAYS[key]
    current_tz = timezone.get_current_timezone()
    if key == 'today':
        start = timezone.make_aware(datetime.combine(now.date(), time.min), current_tz)
    else:
        start_day = (now - timedelta(days=days - 1)).date()
        start = timezone.make_aware(datetime.combine(start_day, time.min), current_tz)
    return key, start, end


def previous_period(start, end):
    delta = end - start
    prev_end = start - timedelta(seconds=1)
    prev_start = prev_end - delta
    return prev_start, prev_end


def _delta_pct(current, previous):
    current_dec = Decimal(current or 0)
    previous_dec = Decimal(previous or 0)
    if previous_dec == 0:
        return Decimal('100.00') if current_dec > 0 else Decimal('0.00')
    return ((current_dec - previous_dec) / previous_dec) * Decimal('100')


def _safe_store_settings(org):
    try:
        return StoreSettings.objects.using('settings_db').filter(organization_id=org.id).first()
    except Exception:
        return None


def get_inventory_metrics(org):
    stock_qs = Stock.objects.filter(variant__product__organization=org).select_related('variant__product')
    qty_total = stock_qs.aggregate(
        total=Coalesce(Sum('quantity', output_field=INT_FIELD), ZERO_INT, output_field=INT_FIELD)
    )['total']

    cost_expr = Coalesce(F('avg_cost'), F('last_cost'), F('variant__cost'), ZERO_DEC, output_field=DECIMAL_12_2)
    inventory_value_expr = ExpressionWrapper(F('quantity') * cost_expr, output_field=DECIMAL_12_2)
    inventory_value = stock_qs.aggregate(
        total=Coalesce(Sum(inventory_value_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
    )['total']

    settings = _safe_store_settings(org)
    low_stock_default = settings.low_stock_default if settings else 3
    low_stock_count = stock_qs.filter(quantity__lte=Coalesce(F('min_alert'), Value(low_stock_default, output_field=INT_FIELD))).count()

    return {
        'active_products': Product.objects.filter(organization=org, is_active=True).count(),
        'stock_total': qty_total or 0,
        'inventory_value': inventory_value or Decimal('0.00'),
        'low_stock_count': low_stock_count,
    }


def get_sales_metrics(org, start, end):
    sales_qs = Sale.objects.filter(organization=org, status=Sale.Status.PAID, created_at__range=(start, end))
    sales_total = sales_qs.aggregate(
        total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
    )['total']
    sale_count = sales_qs.count()
    avg_ticket = (sales_total / sale_count) if sale_count else Decimal('0.00')
    units_sold = SaleItem.objects.filter(sale__in=sales_qs).aggregate(
        total=Coalesce(Sum('qty', output_field=INT_FIELD), ZERO_INT, output_field=INT_FIELD)
    )['total']

    return {
        'sales_count': sale_count,
        'sales_total': sales_total or Decimal('0.00'),
        'avg_ticket': avg_ticket,
        'units_sold': units_sold or 0,
    }


def get_purchase_metrics(org, start, end):
    purchase_qs = PurchaseOrder.objects.filter(
        organization=org,
        status=PurchaseOrder.Status.RECEIVED,
        created_at__range=(start, end),
    )
    purchases_total = purchase_qs.aggregate(
        total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
    )['total']
    return {
        'purchase_count': purchase_qs.count(),
        'purchases_total': purchases_total or Decimal('0.00'),
    }


def get_customer_metrics(org, start, end):
    new_customers = Customer.objects.filter(organization=org, created_at__range=(start, end)).count()
    top_customer = (
        Sale.objects.filter(organization=org, status=Sale.Status.PAID, customer__isnull=False)
        .values('customer__name')
        .annotate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
        .order_by('-total')
        .first()
    )
    return {
        'new_customers': new_customers,
        'top_customer_name': (top_customer or {}).get('customer__name') or 'Sin datos',
        'top_customer_total': (top_customer or {}).get('total') or Decimal('0.00'),
    }


def get_top_products(org, start, end, limit=5):
    return list(
        SaleItem.objects.filter(sale__organization=org, sale__status=Sale.Status.PAID, sale__created_at__range=(start, end))
        .values('variant__product__name', 'variant__product__sku')
        .annotate(total_qty=Coalesce(Sum('qty', output_field=INT_FIELD), ZERO_INT, output_field=INT_FIELD))
        .order_by('-total_qty')[:limit]
    )


def get_top_customers(org, start, end, limit=5):
    return list(
        Sale.objects.filter(organization=org, status=Sale.Status.PAID, created_at__range=(start, end))
        .values('customer__name')
        .annotate(
            orders=Coalesce(Count('id', output_field=INT_FIELD), ZERO_INT, output_field=INT_FIELD),
            total_spent=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2),
        )
        .order_by('-total_spent')[:limit]
    )


def get_low_stock_products(org, limit=5):
    return list(
        Stock.objects.filter(variant__product__organization=org)
        .select_related('variant__product')
        .order_by('quantity')[:limit]
    )


def get_daily_income_chart(org, start, end):
    sales_rows = list(
        Sale.objects.filter(organization=org, status=Sale.Status.PAID, created_at__range=(start, end))
        .annotate(day=TruncDate('created_at', tzinfo=timezone.get_current_timezone()))
        .values('day')
        .annotate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
        .order_by('day')
    )
    totals = {row['day']: row['total'] for row in sales_rows}
    labels, values = [], []
    day = start.date()
    while day <= end.date():
        labels.append(day.isoformat())
        values.append(float(totals.get(day, Decimal('0.00'))))
        day += timedelta(days=1)
    return {'labels': labels, 'values': values}


def get_sales_by_brand_chart(org, start, end):
    rows = list(
        SaleItem.objects.filter(sale__organization=org, sale__status=Sale.Status.PAID, sale__created_at__range=(start, end))
        .values('variant__product__brand__name')
        .annotate(total_qty=Coalesce(Sum('qty', output_field=INT_FIELD), ZERO_INT, output_field=INT_FIELD))
        .order_by('-total_qty')[:8]
    )
    return {
        'labels': [(row['variant__product__brand__name'] or 'Sin marca') for row in rows],
        'values': [row['total_qty'] for row in rows],
    }


def get_dashboard_data(org, range_key):
    cache_key = f'dash:org_{org.id}:{range_key}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    selected_range, start, end = get_date_range(range_key)
    prev_start, prev_end = previous_period(start, end)

    sales = get_sales_metrics(org, start, end)
    sales_prev = get_sales_metrics(org, prev_start, prev_end)
    purchases = get_purchase_metrics(org, start, end)
    purchases_prev = get_purchase_metrics(org, prev_start, prev_end)
    inventory = get_inventory_metrics(org)
    customers = get_customer_metrics(org, start, end)

    cards = [
        {'title': 'Productos activos', 'value': inventory['active_products'], 'delta': Decimal('0.00'), 'is_money': False},
        {'title': 'Stock total', 'value': inventory['stock_total'], 'delta': Decimal('0.00'), 'is_money': False},
        {'title': 'Inventario valorizado', 'value': inventory['inventory_value'], 'delta': Decimal('0.00'), 'is_money': True},
        {'title': 'Bajo stock', 'value': inventory['low_stock_count'], 'delta': Decimal('0.00'), 'is_money': False},
        {'title': 'Ventas del periodo', 'value': sales['sales_count'], 'delta': _delta_pct(sales['sales_count'], sales_prev['sales_count']), 'is_money': False},
        {'title': 'Ingresos', 'value': sales['sales_total'], 'delta': _delta_pct(sales['sales_total'], sales_prev['sales_total']), 'is_money': True},
        {'title': 'Ticket promedio', 'value': sales['avg_ticket'], 'delta': _delta_pct(sales['avg_ticket'], sales_prev['avg_ticket']), 'is_money': True},
        {'title': 'Unidades vendidas', 'value': sales['units_sold'], 'delta': _delta_pct(sales['units_sold'], sales_prev['units_sold']), 'is_money': False},
        {'title': 'Clientes nuevos', 'value': customers['new_customers'], 'delta': Decimal('0.00'), 'is_money': False},
        {'title': 'Compras', 'value': purchases['purchases_total'], 'delta': _delta_pct(purchases['purchases_total'], purchases_prev['purchases_total']), 'is_money': True},
    ]

    data = {
        'selected_range': selected_range,
        'start': start,
        'end': end,
        'cards': cards,
        'top_products': get_top_products(org, start, end),
        'top_customers': get_top_customers(org, start, end),
        'low_stock_products': get_low_stock_products(org),
        'top_customer_name': customers['top_customer_name'],
        'top_customer_total': customers['top_customer_total'],
        'chart_income_daily': get_daily_income_chart(org, start, end),
        'chart_top_products': {
            'labels': [row['variant__product__name'] or 'Sin producto' for row in get_top_products(org, start, end)],
            'values': [row['total_qty'] for row in get_top_products(org, start, end)],
        },
        'chart_brand': get_sales_by_brand_chart(org, start, end),
    }

    data['chart_payload'] = json.dumps(
        {
            'incomeDaily': data['chart_income_daily'],
            'topProducts': data['chart_top_products'],
            'brandSplit': data['chart_brand'],
        }
    )
    cache.set(cache_key, data, 90)
    return data

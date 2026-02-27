import csv
import io
import json
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import DecimalField, ExpressionWrapper, F, IntegerField, Sum, Value
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.inventory.models import Product, Stock
from apps.purchases.models import PurchaseItem, PurchaseOrder
from apps.sales.models import Sale, SaleItem

DECIMAL_12_2 = DecimalField(max_digits=12, decimal_places=2)
INT_FIELD = IntegerField()
ZERO_DEC = Value(Decimal('0.00'), output_field=DECIMAL_12_2)
ZERO_INT = Value(0, output_field=INT_FIELD)
RANGE_DAYS = {'today': 1, '7d': 7, '30d': 30, '90d': 90}


def get_date_range(range_key):
    key = range_key if range_key in RANGE_DAYS else '30d'
    now = timezone.localtime(timezone.now())
    current_tz = timezone.get_current_timezone()
    if key == 'today':
        start = timezone.make_aware(datetime.combine(now.date(), time.min), current_tz)
    else:
        start_day = (now - timedelta(days=RANGE_DAYS[key] - 1)).date()
        start = timezone.make_aware(datetime.combine(start_day, time.min), current_tz)
    return key, start, now


def get_sales_metrics(org, start, end):
    sales_qs = Sale.objects.filter(organization=org, status=Sale.Status.PAID, created_at__range=(start, end))
    ingresos = sales_qs.aggregate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))['total']
    cogs_expr = ExpressionWrapper(
        F('qty') * Coalesce(F('variant__stock__avg_cost'), F('variant__stock__last_cost'), F('variant__cost'), ZERO_DEC, output_field=DECIMAL_12_2),
        output_field=DECIMAL_12_2,
    )
    cogs = SaleItem.objects.filter(sale__in=sales_qs).aggregate(
        total=Coalesce(Sum(cogs_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2)
    )['total']
    return {'ingresos': ingresos or Decimal('0.00'), 'cogs': cogs or Decimal('0.00')}


def get_purchase_metrics(org, start, end):
    purchases = PurchaseOrder.objects.filter(
        organization=org,
        status=PurchaseOrder.Status.RECEIVED,
        created_at__range=(start, end),
    )
    total = purchases.aggregate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))['total']
    return {'gastos': total or Decimal('0.00'), 'purchase_count': purchases.count()}


def get_inventory_metrics(org):
    stock_qs = Stock.objects.filter(variant__product__organization=org)
    inventory_expr = ExpressionWrapper(
        F('quantity') * Coalesce(F('avg_cost'), F('last_cost'), F('variant__cost'), ZERO_DEC, output_field=DECIMAL_12_2),
        output_field=DECIMAL_12_2,
    )
    total = stock_qs.aggregate(total=Coalesce(Sum(inventory_expr, output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))['total']
    return {'inventory_value': total or Decimal('0.00')}


def get_top_selling_products(org, start, end, limit=10):
    return list(
        SaleItem.objects.filter(sale__organization=org, sale__status=Sale.Status.PAID, sale__created_at__range=(start, end))
        .values('variant__product__name', 'variant__product__sku')
        .annotate(total_qty=Coalesce(Sum('qty', output_field=INT_FIELD), ZERO_INT, output_field=INT_FIELD))
        .order_by('-total_qty')[:limit]
    )


def get_unsold_products(org, days=90, limit=10):
    cutoff = timezone.localtime(timezone.now()) - timedelta(days=days)
    sold_ids = SaleItem.objects.filter(sale__organization=org, sale__status=Sale.Status.PAID, sale__created_at__gte=cutoff).values_list('variant__product_id', flat=True)
    return list(Product.objects.filter(organization=org, is_active=True).exclude(id__in=sold_ids).order_by('name')[:limit])


def get_top_purchased_products(org, start, end, limit=10):
    return list(
        PurchaseItem.objects.filter(
            purchase__organization=org,
            purchase__status=PurchaseOrder.Status.RECEIVED,
            purchase__created_at__range=(start, end),
        )
        .values('variant__product__name')
        .annotate(total_qty=Coalesce(Sum('qty', output_field=INT_FIELD), ZERO_INT, output_field=INT_FIELD))
        .order_by('-total_qty')[:limit]
    )


def get_top_suppliers(org, start, end, limit=10):
    return list(
        PurchaseOrder.objects.filter(
            organization=org,
            status=PurchaseOrder.Status.RECEIVED,
            created_at__range=(start, end),
        )
        .values('supplier__name')
        .annotate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
        .order_by('-total')[:limit]
    )


def get_income_vs_expense_chart(org, start, end):
    sales_rows = list(
        Sale.objects.filter(organization=org, status=Sale.Status.PAID, created_at__range=(start, end))
        .annotate(day=TruncDate('created_at', tzinfo=timezone.get_current_timezone()))
        .values('day')
        .annotate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
        .order_by('day')
    )
    purchase_rows = list(
        PurchaseOrder.objects.filter(organization=org, status=PurchaseOrder.Status.RECEIVED, created_at__range=(start, end))
        .annotate(day=TruncDate('created_at', tzinfo=timezone.get_current_timezone()))
        .values('day')
        .annotate(total=Coalesce(Sum('total', output_field=DECIMAL_12_2), ZERO_DEC, output_field=DECIMAL_12_2))
        .order_by('day')
    )
    sales_map = {row['day']: row['total'] for row in sales_rows}
    purchase_map = {row['day']: row['total'] for row in purchase_rows}

    labels, incomes, expenses = [], [], []
    day = start.date()
    while day <= end.date():
        labels.append(day.isoformat())
        incomes.append(float(sales_map.get(day, Decimal('0.00'))))
        expenses.append(float(purchase_map.get(day, Decimal('0.00'))))
        day += timedelta(days=1)
    return {'labels': labels, 'income': incomes, 'expense': expenses}


def get_profit_by_week_chart(org, start, end):
    chart = get_income_vs_expense_chart(org, start, end)
    week_labels, profits = [], []
    income_bucket, expense_bucket = Decimal('0.00'), Decimal('0.00')
    for index, label in enumerate(chart['labels']):
        income_bucket += Decimal(str(chart['income'][index]))
        expense_bucket += Decimal(str(chart['expense'][index]))
        if (index + 1) % 7 == 0 or index == len(chart['labels']) - 1:
            week_labels.append(label)
            profits.append(float(income_bucket - expense_bucket))
            income_bucket = Decimal('0.00')
            expense_bucket = Decimal('0.00')
    return {'labels': week_labels, 'values': profits}


def get_supplier_donut_chart(org, start, end):
    rows = get_top_suppliers(org, start, end, limit=8)
    return {'labels': [r['supplier__name'] or 'Sin proveedor' for r in rows], 'values': [float(r['total']) for r in rows]}


def get_finance_data(org, range_key):
    cache_key = f'finance:org_{org.id}:{range_key}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    selected_range, start, end = get_date_range(range_key)
    sales = get_sales_metrics(org, start, end)
    purchases = get_purchase_metrics(org, start, end)
    inventory = get_inventory_metrics(org)

    gross_profit = sales['ingresos'] - sales['cogs']
    margin_pct = Decimal('0.00') if sales['ingresos'] == 0 else (gross_profit / sales['ingresos']) * Decimal('100')

    top_selling = get_top_selling_products(org, start, end)

    data = {
        'selected_range': selected_range,
        'start': start,
        'end': end,
        'cards': [
            {'title': 'Ingresos', 'value': sales['ingresos'], 'is_money': True},
            {'title': 'Gastos', 'value': purchases['gastos'], 'is_money': True},
            {'title': 'Utilidad bruta estimada', 'value': gross_profit, 'is_money': True},
            {'title': 'Margen %', 'value': margin_pct, 'is_money': False, 'is_percentage': True},
            {'title': 'COGS estimado', 'value': sales['cogs'], 'is_money': True},
            {'title': 'Inventario valorizado', 'value': inventory['inventory_value'], 'is_money': True},
            {'title': 'Órdenes de compra', 'value': purchases['purchase_count'], 'is_money': False},
        ],
        'top_selling_products': top_selling,
        'unsold_products': get_unsold_products(org, days=90),
        'top_purchased_products': get_top_purchased_products(org, start, end),
        'top_suppliers': get_top_suppliers(org, start, end),
        'chart_income_expense': get_income_vs_expense_chart(org, start, end),
        'chart_profit_week': get_profit_by_week_chart(org, start, end),
        'chart_supplier': get_supplier_donut_chart(org, start, end),
    }
    data['chart_top_selling'] = {
        'labels': [row['variant__product__name'] or 'Sin producto' for row in top_selling[:8]],
        'values': [row['total_qty'] for row in top_selling[:8]],
    }
    data['chart_payload'] = json.dumps(
        {
            'incomeExpense': data['chart_income_expense'],
            'profitWeek': data['chart_profit_week'],
            'supplier': data['chart_supplier'],
            'topSelling': data['chart_top_selling'],
        }
    )
    cache.set(cache_key, data, 90)
    return data


def build_sales_csv(org, start, end):
    rows = (
        Sale.objects.filter(organization=org, status=Sale.Status.PAID, created_at__range=(start, end))
        .select_related('customer')
        .order_by('-created_at')
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Número', 'Cliente', 'Total'])
    for sale in rows:
        writer.writerow([timezone.localtime(sale.created_at).strftime('%Y-%m-%d %H:%M'), sale.number, sale.customer.name if sale.customer else 'Sin cliente', sale.total])
    return output.getvalue()


def build_purchase_csv(org, start, end):
    rows = (
        PurchaseOrder.objects.filter(organization=org, status=PurchaseOrder.Status.RECEIVED, created_at__range=(start, end))
        .select_related('supplier')
        .order_by('-created_at')
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Fecha', 'Número', 'Proveedor', 'Total'])
    for purchase in rows:
        writer.writerow([timezone.localtime(purchase.created_at).strftime('%Y-%m-%d %H:%M'), purchase.number, purchase.supplier.name, purchase.total])
    return output.getvalue()

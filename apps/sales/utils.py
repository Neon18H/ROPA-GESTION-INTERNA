from decimal import Decimal


D = Decimal


def _to_decimal(value):
    return value if isinstance(value, Decimal) else D(str(value or '0'))


def compute_sale_totals(items, default_vat_rate=Decimal('0.00')):
    vat_default = _to_decimal(default_vat_rate)
    subtotal = D('0.00')
    tax_total = D('0.00')
    lines = []

    for item in items:
        unit_price = _to_decimal(item.unit_price)
        qty = _to_decimal(item.qty)
        line_subtotal = unit_price * qty

        item_tax = getattr(item, 'tax_rate', None)
        applied_tax_rate = _to_decimal(item_tax) if item_tax is not None else vat_default
        line_tax = (line_subtotal * applied_tax_rate) / D('100.00')
        line_total = line_subtotal + line_tax

        subtotal += line_subtotal
        tax_total += line_tax
        lines.append(
            {
                'item': item,
                'line_subtotal': line_subtotal,
                'line_tax': line_tax,
                'line_total': line_total,
                'applied_tax_rate': applied_tax_rate,
            }
        )

    return {
        'lines': lines,
        'subtotal': subtotal,
        'tax_total': tax_total,
        'total': subtotal + tax_total,
    }

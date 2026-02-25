from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP

COP_QUANT = Decimal('0.01')
USD_QUANT = Decimal('0.01')


def to_decimal(value):
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal('1' if value else '0')
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        value = value.strip()
        if value == '':
            return Decimal('0')
        value = value.replace(',', '')
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def quantize_amount(amount, rounding_policy='HALF_UP', quant=COP_QUANT):
    dec_amount = to_decimal(amount)
    mode = ROUND_HALF_EVEN if rounding_policy == 'BANKERS' else ROUND_HALF_UP
    return dec_amount.quantize(quant, rounding=mode)


def money_cop(amount, rounding_policy='HALF_UP'):
    dec_amount = quantize_amount(amount, rounding_policy=rounding_policy, quant=COP_QUANT)
    formatted = f"{dec_amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"$ {formatted}"


def money_usd(amount, rounding_policy='HALF_UP'):
    if amount is None:
        return '—'
    dec_amount = quantize_amount(amount, rounding_policy=rounding_policy, quant=USD_QUANT)
    return f"US$ {dec_amount:,.2f}"


def convert_cop_to_usd(cop_amount, fx_rate, rounding_policy='HALF_UP'):
    cop_amount_dec = to_decimal(cop_amount)
    fx_rate_dec = to_decimal(fx_rate)
    if fx_rate_dec <= 0:
        return None
    return quantize_amount(cop_amount_dec / fx_rate_dec, rounding_policy=rounding_policy, quant=USD_QUANT)

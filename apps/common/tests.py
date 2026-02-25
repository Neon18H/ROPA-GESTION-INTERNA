from decimal import Decimal

from django.test import SimpleTestCase

from apps.common.money import convert_cop_to_usd, money_cop, money_usd, quantize_amount, to_decimal


class MoneyFormattingTests(SimpleTestCase):
    def test_money_formatting(self):
        self.assertEqual(to_decimal('1234.50'), Decimal('1234.50'))
        self.assertEqual(money_cop(Decimal('1234567.89')), '$ 1.234.567,89')
        self.assertEqual(money_usd(Decimal('1234.56')), 'US$ 1,234.56')
        self.assertEqual(convert_cop_to_usd(Decimal('4000'), Decimal('0')), None)
        self.assertEqual(convert_cop_to_usd(Decimal('4000'), Decimal('4000')), Decimal('1.00'))
        self.assertEqual(quantize_amount(Decimal('10.125'), 'HALF_UP'), Decimal('10.13'))

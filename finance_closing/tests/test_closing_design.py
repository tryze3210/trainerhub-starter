from decimal import Decimal


def test_month_end_snapshot_payload_shape():
    payload = {
        'ledger': {
            'platform_commission_accrued': '100.00',
            'trainer_payable_balance': '900.00',
        },
        'generated_from_period': '2026-03',
    }
    assert payload['ledger']['platform_commission_accrued'] == '100.00'


def test_statement_net_payable_formula():
    gross = Decimal('1000.00')
    refunds = Decimal('100.00')
    commission = Decimal('150.00')
    fees = Decimal('20.00')
    reserve = Decimal('30.00')
    net = gross - refunds - commission - fees - reserve
    assert net == Decimal('700.00')

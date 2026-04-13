# v21 accounting test scenarios

## 1. One-time order payment split

Given:
- order total = 10,000.00
- trainer share = 80%
- platform commission = 20%

Expect ledger entries:
- cash_in credit 10,000.00
- trainer_payable credit 8,000.00
- platform_commission_revenue credit 2,000.00

## 2. Partial refund propagation

Given:
- original gross = 10,000.00
- refund = 2,500.00

Expect reversal ratio = 25%
Expect reversal entries:
- cash_in debit 2,500.00
- trainer_payable debit 2,000.00
- platform_commission_revenue debit 500.00

## 3. Full subscription cycle renewal

Given:
- monthly renewal = 3,000.00
- trainer share = 70%
- platform commission = 30%

Expect:
- cash_in credit 3,000.00
- trainer_payable credit 2,100.00
- platform_commission_revenue credit 900.00

## 4. Payout allocation

Given trainer payable credits:
- 2,000.00
- 3,000.00

When create payout batch amount=4,500.00
Expect:
- first entry allocated fully 2,000.00
- second entry allocated partially 2,500.00
- batch planned_amount = 4,500.00

## 5. Payout finalization

When batch marked paid
Expect:
- trainer_payable debit entries for allocated amounts
- payout item statuses become `paid`
- batch status becomes `paid`

## 6. Idempotency

Calling the same posting service twice with same source must fail by unique `idempotency_key`.
Application service should treat this as already posted and return existing state.

## 7. Entitlement reversal without refund

When entitlement is revoked by moderation/business rule
Expect:
- trainer_payable debit reversal
- platform_commission_revenue debit reversal
- original cash_in preserved unless separate refund event exists

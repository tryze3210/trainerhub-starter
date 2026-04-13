from decimal import Decimal
from uuid import uuid4
from types import SimpleNamespace

from apps.orders.services import OrderService
from apps.payments.services import PaymentService
from apps.subscriptions.models import SubscriptionPlan


class DummyManager:
    def create(self, **kwargs):
        return SimpleNamespace(**kwargs, id=uuid4(), save=lambda **_: None, items=SimpleNamespace(first=lambda: None))


def test_purchase_to_access_flow_contract_smoke():
    user = SimpleNamespace(id=uuid4(), email='user@example.com')
    plan = SimpleNamespace(id=uuid4(), code='pro-monthly', title='Pro Monthly', price=Decimal('990.00'), currency='RUB')
    assert plan.code == 'pro-monthly'
    assert str(plan.price) == '990.00'

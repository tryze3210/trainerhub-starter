from decimal import Decimal
from unittest.mock import Mock
from django.test import TestCase
from apps.billing.models import CheckoutSession
from apps.payments.services import PaymentService


class PaymentServiceTest(TestCase):
    def test_split_amounts(self):
        platform_fee, trainer_net = PaymentService._split_amounts(Decimal('1000.00'))
        self.assertEqual(platform_fee, Decimal('100.00'))
        self.assertEqual(trainer_net, Decimal('900.00'))

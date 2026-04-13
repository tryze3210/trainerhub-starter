from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.subscriptions.models import SubscriptionPlan
from apps.subscriptions.services import SubscriptionService
from apps.entitlements.models import Entitlement

class SubscriptionServiceTestCase(TestCase):
    def test_activate_subscription_grants_entitlement(self):
        user = get_user_model().objects.create_user(email='test@example.com', password='pass')
        plan = SubscriptionPlan.objects.create(
            trainer_id='8c8d4a46-e257-451b-aad8-df2f0ecbfc41',
            title='Monthly',
            price='1000.00',
            billing_period='month',
        )

        subscription = SubscriptionService.activate_subscription(user=user, plan=plan)

        self.assertEqual(subscription.status, 'active')
        self.assertTrue(
            Entitlement.objects.filter(user=user, source='subscription', source_reference=str(subscription.id), is_active=True).exists()
        )

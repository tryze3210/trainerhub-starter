from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.comms.constants import NotificationCategory, NotificationChannel, TemplateStatus
from apps.comms.models import NotificationTemplate
from apps.comms.services import NotificationOrchestratorService


class NotificationOrchestratorServiceTests(TestCase):
    def test_queue_message_from_active_template(self):
        user = get_user_model().objects.create_user(username="user1", email="u@example.com", password="x")
        NotificationTemplate.objects.create(
            key="order_paid",
            category=NotificationCategory.TRANSACTIONAL,
            channel=NotificationChannel.EMAIL,
            locale="en",
            status=TemplateStatus.ACTIVE,
            subject_template="Order #${order_id} paid",
            title_template="Payment received",
            body_template="Hello ${name}",
        )
        message = NotificationOrchestratorService().queue_from_template(
            user=user,
            template_key="order_paid",
            channel=NotificationChannel.EMAIL,
            category=NotificationCategory.TRANSACTIONAL,
            context={"order_id": 10, "name": "Vlad"},
            payload={"order_id": 10},
            event_key="order.paid",
            idempotency_key="order-paid-10",
        )
        self.assertEqual(message.subject, "Order #10 paid")
        self.assertEqual(message.title, "Payment received")

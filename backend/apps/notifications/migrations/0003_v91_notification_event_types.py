from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_v33_notification_delivery'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationdelivery',
            name='type',
            field=models.CharField(
                choices=[
                    ('order_paid', 'Order paid'),
                    ('payment_succeeded', 'Payment succeeded'),
                    ('payment_failed', 'Payment failed'),
                    ('payment_refunded', 'Payment refunded'),
                    ('access_granted', 'Access granted'),
                    ('subscription_activated', 'Subscription activated'),
                    ('subscription_expiring', 'Subscription expiring'),
                    ('payout_paid', 'Payout paid'),
                    ('admin_announcement', 'Admin announcement'),
                ],
                max_length=50,
            ),
        ),
    ]

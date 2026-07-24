import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.users.models import User
from apps.customers.models import CustomerProfile
from apps.trainers.models import TrainerProfile


class Command(BaseCommand):
    help = "Create demo customer and trainer users for local bootstrap"

    def handle(self, *args, **options):
        if getattr(settings, "IS_PRODUCTION", False) and os.getenv("ALLOW_DEMO_SEED") != "1":
            raise CommandError("Demo users are disabled in production. Set ALLOW_DEMO_SEED=1 only for an intentional smoke dataset.")

        customer, _ = User.objects.get_or_create(
            email="customer@example.com",
            defaults={"role": User.Roles.CUSTOMER, "first_name": "Demo", "last_name": "Customer"},
        )
        if not customer.has_usable_password():
            customer.set_password("demo12345")
            customer.save(update_fields=["password"])
        CustomerProfile.objects.get_or_create(user=customer, defaults={"display_name": "Demo Customer"})

        trainer, _ = User.objects.get_or_create(
            email="trainer@example.com",
            defaults={"role": User.Roles.TRAINER, "first_name": "Demo", "last_name": "Trainer"},
        )
        if not trainer.has_usable_password():
            trainer.set_password("demo12345")
            trainer.save(update_fields=["password"])
        CustomerProfile.objects.get_or_create(user=trainer, defaults={"display_name": "Demo Trainer"})
        TrainerProfile.objects.get_or_create(
            user=trainer,
            defaults={"slug": "demo-trainer", "display_name": "Demo Trainer", "headline": "Dance Fitness Coach", "status": "approved"},
        )
        self.stdout.write(self.style.SUCCESS("Demo users ensured."))

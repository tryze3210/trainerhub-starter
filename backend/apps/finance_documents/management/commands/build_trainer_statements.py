from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.finance_documents.services.statements import TrainerStatementService

User = get_user_model()


class Command(BaseCommand):
    help = "Build trainer finance statements for the current month"

    def handle(self, *args, **options):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        service = TrainerStatementService()
        count = 0
        for trainer in User.objects.filter(is_active=True):
            service.build_monthly_statement(trainer=trainer, period_start=month_start, period_end=today)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Built {count} trainer statements"))

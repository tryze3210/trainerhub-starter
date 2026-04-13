from django.core.management.base import BaseCommand

from apps.finance_reporting.services.reconciliation import FinanceReconciliationService


class Command(BaseCommand):
    help = "Rebuild finance reconciliation snapshots"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **options):
        FinanceReconciliationService().bootstrap_recent_snapshots(days=options["days"])
        self.stdout.write(self.style.SUCCESS("Finance reconciliation snapshots rebuilt."))

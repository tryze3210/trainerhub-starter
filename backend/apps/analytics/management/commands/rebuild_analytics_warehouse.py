from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.services.kpi_builder import AnalyticsWarehouseBuilder


class Command(BaseCommand):
    help = 'Rebuild analytics warehouse tables from transactional and raw analytics-event data.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--full', action='store_true')
        parser.add_argument('--trigger', type=str, default='manual')

    def handle(self, *args, **options):
        builder = AnalyticsWarehouseBuilder()
        trigger = options['trigger']
        if options['full']:
            rows_written = builder.rebuild_full(trigger=trigger)
        else:
            days = max(1, options['days'])
            end_date = timezone.localdate()
            start_date = end_date - timedelta(days=days - 1)
            rows_written = builder.rebuild(start_date=start_date, end_date=end_date, trigger=trigger)
        self.stdout.write(self.style.SUCCESS(f'Analytics warehouse rebuild completed. Rows written: {rows_written}'))

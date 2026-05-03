from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.ops.reconciliation_snapshots import capture_reconciliation_snapshot


class Command(BaseCommand):
    help = 'Capture a persisted admin reconciliation snapshot.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--source', default='scheduled', choices=['manual', 'scheduled', 'repair', 'ci'])
        parser.add_argument('--correlation-id', default='')
        parser.add_argument('--json', action='store_true')
        parser.add_argument('--fail-on-critical', action='store_true')

    def handle(self, *args, **options):
        payload = capture_reconciliation_snapshot(
            limit=options['limit'],
            source=options['source'],
            correlation_id=options.get('correlation_id') or 'cmd:capture_reconciliation_snapshot',
        )
        if options['json']:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, default=str))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Captured reconciliation snapshot {payload['id']} "
                    f"status={payload['status']} total_issues={payload['total_issues']} "
                    f"critical={payload['critical_count']}"
                )
            )
        if options['fail_on_critical'] and payload.get('critical_count', 0):
            raise CommandError('Reconciliation snapshot contains critical issues.')

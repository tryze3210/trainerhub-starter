from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.ops.reconciliation_snapshots import (
    capture_reconciliation_snapshot,
    capture_reconciliation_snapshot_if_due,
)


class Command(BaseCommand):
    help = 'Capture a persisted admin reconciliation snapshot.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--source', default='scheduled', choices=['manual', 'scheduled', 'repair', 'ci'])
        parser.add_argument('--correlation-id', default='')
        parser.add_argument('--json', action='store_true')
        parser.add_argument('--fail-on-critical', action='store_true')
        parser.add_argument('--if-due', action='store_true')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--min-age-minutes', type=int, default=60)

    def handle(self, *args, **options):
        if options['if_due']:
            payload = capture_reconciliation_snapshot_if_due(
                limit=options['limit'],
                source=options['source'],
                min_age_minutes=options['min_age_minutes'],
                force=options['force'],
                correlation_id=options.get('correlation_id') or 'cmd:capture_reconciliation_snapshot',
            )
        else:
            payload = capture_reconciliation_snapshot(
                limit=options['limit'],
                source=options['source'],
                correlation_id=options.get('correlation_id') or 'cmd:capture_reconciliation_snapshot',
            )

        if options['json']:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, default=str))
        elif payload.get('status') == 'skipped':
            self.stdout.write(
                self.style.WARNING(
                    'Skipped reconciliation snapshot: '
                    f"reason={payload.get('reason')} source={payload.get('source')} "
                    f"next_due_at={payload.get('next_due_at')}"
                )
            )
        elif payload.get('status') == 'captured' and payload.get('snapshot'):
            snapshot = payload['snapshot']
            self.stdout.write(
                self.style.SUCCESS(
                    f"Captured reconciliation snapshot {snapshot['id']} "
                    f"status={snapshot['status']} total_issues={snapshot['total_issues']} "
                    f"critical={snapshot['critical_count']}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Captured reconciliation snapshot {payload['id']} "
                    f"status={payload['status']} total_issues={payload['total_issues']} "
                    f"critical={payload['critical_count']}"
                )
            )

        snapshot_payload = payload.get('snapshot') if payload.get('snapshot') else payload
        critical_count = int(snapshot_payload.get('critical_count') or 0)
        if options['fail_on_critical'] and critical_count:
            raise CommandError('Reconciliation snapshot contains critical issues.')

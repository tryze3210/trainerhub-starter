from __future__ import annotations

import json

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from apps.ops.operations_readiness import get_ops_production_readiness


def _json_default(value):
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


class Command(BaseCommand):
    help = 'Check production readiness for the ops/reconciliation surface.'

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', dest='as_json', help='Render machine-readable JSON output.')
        parser.add_argument('--no-commands', action='store_true', help='Omit smoke command suite from the output.')
        parser.add_argument('--no-recommendations', action='store_true', help='Omit recommendations from the output.')
        parser.add_argument(
            '--fail-on-degraded',
            action='store_true',
            help='Exit with a non-zero status when readiness is degraded or critical.',
        )

    def handle(self, *args, **options):
        payload = get_ops_production_readiness(
            include_commands=not options['no_commands'],
            include_recommendations=not options['no_recommendations'],
        )

        if options['as_json']:
            self.stdout.write(json.dumps(payload, default=_json_default, ensure_ascii=False, indent=2))
        else:
            summary = payload['summary']
            self.stdout.write(f"Ops readiness: {payload['status']} ({payload['version']})")
            self.stdout.write(
                'Checks: '
                f"ok={summary['ok_count']} "
                f"warning={summary['warning_count']} "
                f"degraded={summary['degraded_count']} "
                f"critical={summary['critical_count']}"
            )
            for check in payload['checks']:
                status = check.get('status')
                marker = '✓' if status == 'ok' else '!'
                self.stdout.write(f"{marker} [{status}] {check.get('category')}::{check.get('key')} - {check.get('title')}")
                if check.get('detail'):
                    self.stdout.write(f"    {check['detail']}")

        if options['fail_on_degraded'] and payload['status'] in {'degraded', 'critical'}:
            raise SystemExit(1)

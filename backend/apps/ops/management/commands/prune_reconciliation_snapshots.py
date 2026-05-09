from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from apps.ops.reconciliation_snapshots import prune_reconciliation_snapshots


class Command(BaseCommand):
    help = 'Preview or prune old persisted reconciliation snapshots according to retention policy.'

    def add_arguments(self, parser):
        parser.add_argument('--source', default='', choices=['', 'manual', 'scheduled', 'repair', 'ci'])
        parser.add_argument('--scheduled-days', type=int, default=45)
        parser.add_argument('--repair-days', type=int, default=180)
        parser.add_argument('--manual-days', type=int, default=365)
        parser.add_argument('--ci-days', type=int, default=14)
        parser.add_argument('--keep-min-per-source', type=int, default=25)
        parser.add_argument('--max-candidates', type=int, default=500)
        parser.add_argument('--json', action='store_true')
        parser.add_argument('--commit', action='store_true', help='Actually delete candidates. Default is dry-run preview.')
        parser.add_argument('--hide-candidates', action='store_true')

    def handle(self, *args, **options):
        payload = prune_reconciliation_snapshots(
            source=options['source'],
            scheduled_days=options['scheduled_days'],
            repair_days=options['repair_days'],
            manual_days=options['manual_days'],
            ci_days=options['ci_days'],
            keep_min_per_source=options['keep_min_per_source'],
            max_candidates=options['max_candidates'],
            include_candidates=not options['hide_candidates'],
            dry_run=not options['commit'],
        )

        if options['json']:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, default=str))
            return

        summary = payload['summary']
        if payload['status'] == 'pruned':
            self.stdout.write(
                self.style.SUCCESS(
                    f"Pruned {summary['deleted_count']} reconciliation snapshots "
                    f"from {summary['candidate_count']} candidates."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {summary['candidate_count']} reconciliation snapshots are eligible for pruning; "
                    f"{summary['returned_candidate_count']} candidates returned. Use --commit to delete."
                )
            )

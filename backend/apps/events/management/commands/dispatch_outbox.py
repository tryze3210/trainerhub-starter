from __future__ import annotations

import json
import time
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.events.services import DomainEventService


class Command(BaseCommand):
    help = 'Dispatch pending transactional outbox messages through registered event handlers.'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=100, help='Maximum number of outbox messages to claim per batch. Default: 100.')
        parser.add_argument('--max-batches', type=int, default=1, help='Maximum number of batches to process. Use 0 with --loop for unlimited. Default: 1.')
        parser.add_argument('--loop', action='store_true', help='Keep polling until max-batches is reached or no messages are available.')
        parser.add_argument('--sleep-seconds', type=float, default=1.0, help='Delay between loop iterations when --loop is enabled. Default: 1.0.')
        parser.add_argument('--fail-on-error', action='store_true', help='Exit with a non-zero status if any outbox message failed during dispatch.')
        parser.add_argument('--json', action='store_true', help='Print only a machine-readable JSON summary.')

    def handle(self, *args, **options):
        batch_size = self._positive_int(options['batch_size'], option='--batch-size')
        max_batches = self._non_negative_int(options['max_batches'], option='--max-batches')
        sleep_seconds = max(float(options['sleep_seconds']), 0.0)
        loop = bool(options['loop'])
        json_output = bool(options['json'])
        fail_on_error = bool(options['fail_on_error'])

        service = DomainEventService()
        totals: dict[str, Any] = {
            'batches': 0,
            'claimed': 0,
            'processed': 0,
            'failed': 0,
            'loop': loop,
            'batch_size': batch_size,
        }

        while True:
            result = service.dispatch_pending_batch(batch_size=batch_size)
            totals['batches'] += 1
            totals['claimed'] += int(result.get('claimed') or 0)
            totals['processed'] += int(result.get('processed') or 0)
            totals['failed'] += int(result.get('failed') or 0)

            if not json_output and options.get('verbosity', 1) > 1:
                self.stdout.write(
                    'batch={batch} claimed={claimed} processed={processed} failed={failed}'.format(
                        batch=totals['batches'],
                        claimed=result.get('claimed', 0),
                        processed=result.get('processed', 0),
                        failed=result.get('failed', 0),
                    )
                )

            no_more_messages = int(result.get('claimed') or 0) == 0
            reached_batch_limit = max_batches > 0 and totals['batches'] >= max_batches
            if not loop or no_more_messages or reached_batch_limit:
                break
            if sleep_seconds:
                time.sleep(sleep_seconds)

        if json_output:
            self.stdout.write(json.dumps(totals, sort_keys=True))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    'Outbox dispatch complete: batches={batches} claimed={claimed} processed={processed} failed={failed}'.format(
                        **totals
                    )
                )
            )

        if fail_on_error and totals['failed']:
            raise CommandError(f"Outbox dispatch failed for {totals['failed']} message(s).")

    @staticmethod
    def _positive_int(value: int, *, option: str) -> int:
        value = int(value)
        if value < 1:
            raise CommandError(f'{option} must be greater than zero.')
        return value

    @staticmethod
    def _non_negative_int(value: int, *, option: str) -> int:
        value = int(value)
        if value < 0:
            raise CommandError(f'{option} cannot be negative.')
        return value

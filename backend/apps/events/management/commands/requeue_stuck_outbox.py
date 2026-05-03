from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.events.services import DomainEventService


class Command(BaseCommand):
    help = 'Requeue stale outbox messages left in processing state after worker interruption.'

    def add_arguments(self, parser):
        parser.add_argument('--older-than-minutes', type=int, default=15, help='Requeue processing messages locked earlier than this threshold. Default: 15.')
        parser.add_argument('--limit', type=int, default=100, help='Maximum number of stuck messages to requeue. Default: 100.')
        parser.add_argument('--json', action='store_true', help='Print only a machine-readable JSON summary.')

    def handle(self, *args, **options):
        older_than_minutes = self._positive_int(options['older_than_minutes'], option='--older-than-minutes')
        limit = self._positive_int(options['limit'], option='--limit')

        result = DomainEventService().requeue_stuck_processing(
            older_than_minutes=older_than_minutes,
            limit=limit,
        )
        result = {
            'older_than_minutes': older_than_minutes,
            'limit': limit,
            **result,
        }

        if options['json']:
            self.stdout.write(json.dumps(result, sort_keys=True))
        else:
            self.stdout.write(self.style.SUCCESS('Outbox requeue complete: requeued={requeued}'.format(**result)))

    @staticmethod
    def _positive_int(value: int, *, option: str) -> int:
        value = int(value)
        if value < 1:
            raise CommandError(f'{option} must be greater than zero.')
        return value

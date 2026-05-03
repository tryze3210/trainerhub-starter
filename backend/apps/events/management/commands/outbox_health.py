from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.events.health import get_outbox_health


class Command(BaseCommand):
    help = 'Print event outbox health for Docker healthchecks, cron and CI smoke checks.'

    def add_arguments(self, parser):
        parser.add_argument('--max-pending-age-minutes', type=int, default=15)
        parser.add_argument('--max-processing-age-minutes', type=int, default=15)
        parser.add_argument('--max-dead-messages', type=int, default=0)
        parser.add_argument('--max-failed-messages', type=int, default=50)
        parser.add_argument('--json', action='store_true', dest='as_json')
        parser.add_argument('--fail-on-unhealthy', action='store_true')

    def handle(self, *args, **options):
        health = get_outbox_health(
            max_pending_age_minutes=options['max_pending_age_minutes'],
            max_processing_age_minutes=options['max_processing_age_minutes'],
            max_dead_messages=options['max_dead_messages'],
            max_failed_messages=options['max_failed_messages'],
        )

        if options['as_json']:
            self.stdout.write(json.dumps(health, ensure_ascii=False, sort_keys=True))
        else:
            outbox = health['outbox']
            self.stdout.write(f"outbox status: {health['status']}")
            self.stdout.write(
                'messages: '
                f"pending={outbox['pending_count']} "
                f"processing={outbox['processing_count']} "
                f"failed={outbox['failed_count']} "
                f"dead={outbox['dead_count']} "
                f"processed={outbox['processed_count']}"
            )
            for reason in health['reasons']:
                self.stdout.write(f'- {reason}')

        if options['fail_on_unhealthy'] and not health['ok']:
            raise CommandError(f"outbox unhealthy: {health['status']}")

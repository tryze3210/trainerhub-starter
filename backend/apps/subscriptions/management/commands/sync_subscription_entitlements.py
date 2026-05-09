from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from apps.subscriptions.lifecycle import SubscriptionLifecycleService


class Command(BaseCommand):
    help = 'Synchronize subscription-backed entitlements according to v8.46 lifecycle policy.'

    def add_arguments(self, parser):
        parser.add_argument('--subscription-id', dest='subscription_id', default=None)
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--json', action='store_true', dest='as_json')

    def handle(self, *args, **options):
        payload = SubscriptionLifecycleService.reconcile_subscriptions(
            limit=max(1, min(int(options.get('limit') or 100), 500)),
            subscription_id=options.get('subscription_id') or None,
            actor=None,
            request=None,
        )
        if options.get('as_json'):
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    'subscription entitlements checked={checked_count}, granted_or_refreshed={granted_or_refreshed_count}, revoked={revoked_count}, noop={noop_count}'.format(
                        **payload
                    )
                )
            )

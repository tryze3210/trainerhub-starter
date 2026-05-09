from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError
from rest_framework.renderers import JSONRenderer

from apps.payouts.readiness import PayoutReadinessOptions, build_admin_payout_readiness


class Command(BaseCommand):
    help = "Check admin payout operations readiness."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
        parser.add_argument("--fail-on-degraded", action="store_true", help="Exit non-zero when status is degraded or critical.")
        parser.add_argument("--skip-projection", action="store_true", help="Skip payout projection health check.")
        parser.add_argument("--skip-reconciliation", action="store_true", help="Skip payout reconciliation health check.")
        parser.add_argument("--skip-recommendations", action="store_true", help="Omit recommendations from output.")

    def handle(self, *args, **options):
        payload = build_admin_payout_readiness(
            options=PayoutReadinessOptions(
                include_projection=not options["skip_projection"],
                include_reconciliation=not options["skip_reconciliation"],
                include_recommendations=not options["skip_recommendations"],
            )
        )
        if options["json"]:
            self.stdout.write(JSONRenderer().render(payload).decode("utf-8"))
        else:
            summary = payload["summary"]
            self.stdout.write(f"Payout readiness: {payload['status']}")
            self.stdout.write(
                "Checks: {ok}/{total} ok, warnings={warnings}, critical={critical}".format(
                    ok=summary["ok_count"],
                    total=summary["checks_total"],
                    warnings=summary["warning_count"],
                    critical=summary["critical_count"],
                )
            )
            for item in payload["checks"]:
                self.stdout.write(f"- {item['status']} {item['code']}: {item['message']}")
        if options["fail_on_degraded"] and payload["status"] in {"degraded", "critical"}:
            raise CommandError(f"Payout readiness is {payload['status']}.")

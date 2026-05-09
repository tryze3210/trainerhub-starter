from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.trainers.application_readiness import build_trainer_application_readiness


class Command(BaseCommand):
    help = "Check trainer application/onboarding readiness and output a production smoke report."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="as_json", help="Output JSON payload.")
        parser.add_argument("--limit", type=int, default=50, help="Maximum number of issue samples to include.")
        parser.add_argument("--stale-after-days", type=int, default=7, help="Review queue age threshold in days.")
        parser.add_argument("--no-samples", action="store_true", help="Do not include full application samples in issues.")
        parser.add_argument("--no-recommendations", action="store_true", help="Do not include recommendations.")
        parser.add_argument(
            "--fail-on-degraded",
            action="store_true",
            help="Exit with non-zero status when readiness status is warning/degraded.",
        )

    def handle(self, *args, **options):
        payload = build_trainer_application_readiness(
            limit=options["limit"],
            stale_after_days=options["stale_after_days"],
            include_samples=not options["no_samples"],
            include_recommendations=not options["no_recommendations"],
        )

        if options["as_json"]:
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            summary = payload["summary"]
            self.stdout.write(f"Trainer application readiness: {payload['status']}")
            self.stdout.write(f"Applications: {summary['total_applications']}")
            self.stdout.write(f"Review queue: {summary['review_queue_count']}")
            self.stdout.write(f"Approved: {summary['approved_count']}")
            self.stdout.write(f"Dashboard-ready: {summary['dashboard_ready_count']}")
            self.stdout.write(
                f"Issues: {summary['issue_count']} "
                f"(critical={summary['critical_count']}, warning={summary['warning_count']}, info={summary['info_count']})"
            )
            for issue in payload["issues"][:10]:
                self.stdout.write(f"- [{issue['severity']}] {issue['code']}: {issue['message']}")

        if options["fail_on_degraded"] and payload["status"] not in {"healthy", "empty"}:
            raise CommandError(f"Trainer application readiness is {payload['status']}")

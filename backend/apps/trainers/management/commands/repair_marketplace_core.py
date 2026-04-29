from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.trainers.services.maintenance import TrainerMarketplaceMaintenanceService


class Command(BaseCommand):
    help = "Inspect or repair trainer onboarding, moderation queue and approved trainer access consistency."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply repairs. Without this flag the command runs in dry-run mode.",
        )
        parser.add_argument(
            "--inspect-only",
            action="store_true",
            help="Only print current consistency counters without running the repair planner.",
        )

    def handle(self, *args, **options):
        service = TrainerMarketplaceMaintenanceService()

        inspection = service.inspect()
        self.stdout.write(self.style.MIGRATE_HEADING("Marketplace core inspection"))
        for section, counters in inspection.items():
            self.stdout.write(f"[{section}]")
            for key, value in counters.items():
                self.stdout.write(f"  {key}: {value}")

        if options["inspect_only"]:
            return

        dry_run = not options["apply"]
        report = service.repair(dry_run=dry_run).as_dict()
        self.stdout.write(self.style.MIGRATE_HEADING("Marketplace core repair report"))
        for key, value in report.items():
            if key == "errors":
                continue
            self.stdout.write(f"{key}: {value}")

        errors = report.get("errors") or []
        if errors:
            self.stdout.write(self.style.WARNING("Errors:"))
            for item in errors:
                self.stdout.write(f"  {item}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run only. Re-run with --apply to persist changes."))
        else:
            self.stdout.write(self.style.SUCCESS("Marketplace core repairs applied."))

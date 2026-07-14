from django.core.management.base import BaseCommand
from django.db import transaction

from apps.disputes.models import ChargebackOperation, DisputeCase, DisputeEvent, RefundReview, SupportInboxItem


class Command(BaseCommand):
    help = "Repair derived dispute records used by admin queues and operations dashboards."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report missing derived records without writing changes.",
        )

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        summary = {
            "cases_checked": 0,
            "created_events": 0,
            "refund_reviews": 0,
            "chargeback_operations": 0,
            "support_inbox_items": 0,
        }

        with transaction.atomic():
            for case in DisputeCase.objects.select_related("opened_by").order_by("created_at"):
                summary["cases_checked"] += 1

                if not DisputeEvent.objects.filter(
                    dispute_case=case,
                    event_type=DisputeEvent.EVENT_CREATED,
                ).exists():
                    summary["created_events"] += 1
                    if not dry_run:
                        DisputeEvent.objects.create(
                            dispute_case=case,
                            actor=case.opened_by,
                            event_type=DisputeEvent.EVENT_CREATED,
                            body=case.summary,
                            payload={"rebuild": True},
                        )

                if case.dispute_type == DisputeCase.TYPE_REFUND:
                    exists = RefundReview.objects.filter(dispute_case=case).exists()
                    if not exists:
                        summary["refund_reviews"] += 1
                        if not dry_run:
                            RefundReview.objects.create(dispute_case=case)

                if case.dispute_type == DisputeCase.TYPE_CHARGEBACK:
                    exists = ChargebackOperation.objects.filter(dispute_case=case).exists()
                    if not exists:
                        summary["chargeback_operations"] += 1
                        if not dry_run:
                            ChargebackOperation.objects.create(dispute_case=case)

                if not SupportInboxItem.objects.filter(dispute_case=case).exists():
                    summary["support_inbox_items"] += 1
                    if not dry_run:
                        SupportInboxItem.objects.create(dispute_case=case)

            if dry_run:
                transaction.set_rollback(True)

        mode = "dry-run" if dry_run else "applied"
        self.stdout.write(
            self.style.SUCCESS(
                "Disputes read-side rebuild {mode}: "
                "cases={cases_checked} created_events={created_events} "
                "refund_reviews={refund_reviews} chargeback_operations={chargeback_operations} "
                "support_inbox_items={support_inbox_items}".format(mode=mode, **summary)
            )
        )

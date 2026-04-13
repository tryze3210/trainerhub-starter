from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Placeholder for rebuilding disputes read-side projections."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Disputes read-side rebuild placeholder completed."))

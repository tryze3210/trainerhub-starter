from django.conf import settings
from django.core.management.base import BaseCommand
from apps.platform_settings.models import PlatformSettings


class Command(BaseCommand):
    help = "Ensure singleton platform settings row exists"

    def handle(self, *args, **options):
        PlatformSettings.objects.get_or_create(
            default_currency="RUB",
            defaults={
                "global_commission_rate": settings.GLOBAL_COMMISSION_RATE,
                "media_presigned_read_ttl_seconds": settings.MEDIA_READ_TTL_SECONDS,
                "media_upload_ttl_seconds": settings.MEDIA_UPLOAD_TTL_SECONDS,
            },
        )
        self.stdout.write(self.style.SUCCESS("Platform settings ensured."))

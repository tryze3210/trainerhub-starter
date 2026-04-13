from decimal import Decimal
import uuid

from django.db import models


class DailyPlatformKPI(models.Model):
    date = models.DateField(unique=True)

    total_orders = models.PositiveIntegerField(default=0)
    paid_orders = models.PositiveIntegerField(default=0)
    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    paid_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    total_new_customers = models.PositiveIntegerField(default=0)
    total_new_trainers = models.PositiveIntegerField(default=0)
    active_subscriptions = models.PositiveIntegerField(default=0)
    new_subscriptions = models.PositiveIntegerField(default=0)

    arppu = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    conversion_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_daily_platform_kpi"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date"], name="analytics_plat_date_idx"),
        ]

    def __str__(self) -> str:
        return f"Platform KPI {self.date}"


class DailyTrainerKPI(models.Model):
    date = models.DateField()
    trainer_id = models.UUIDField(db_index=True)

    total_orders = models.PositiveIntegerField(default=0)
    paid_orders = models.PositiveIntegerField(default=0)
    gross_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    paid_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    new_customers = models.PositiveIntegerField(default=0)
    active_subscribers = models.PositiveIntegerField(default=0)
    new_subscriptions = models.PositiveIntegerField(default=0)
    arppu = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_daily_trainer_kpi"
        ordering = ["-date", "trainer_id"]
        unique_together = (("date", "trainer_id"),)
        indexes = [
            models.Index(fields=["date", "trainer_id"], name="analytics_trainer_day_idx"),
            models.Index(fields=["trainer_id", "date"], name="analytics_trainer_date_idx"),
        ]

    def __str__(self) -> str:
        return f"Trainer KPI {self.trainer_id} {self.date}"


class DailyPlatformFunnel(models.Model):
    date = models.DateField(unique=True)
    signups = models.PositiveIntegerField(default=0)
    ordering_customers = models.PositiveIntegerField(default=0)
    paid_customers = models.PositiveIntegerField(default=0)
    new_subscribers = models.PositiveIntegerField(default=0)

    signup_to_order_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))
    order_to_paid_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))
    paid_to_subscription_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_daily_platform_funnel"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date"], name="analytics_funnel_date_idx"),
        ]

    def __str__(self) -> str:
        return f"Platform Funnel {self.date}"


class DailyUserCohortRetention(models.Model):
    cohort_date = models.DateField(unique=True)
    cohort_size = models.PositiveIntegerField(default=0)
    retained_day_0 = models.PositiveIntegerField(default=0)
    retained_day_1 = models.PositiveIntegerField(default=0)
    retained_day_7 = models.PositiveIntegerField(default=0)
    retained_day_30 = models.PositiveIntegerField(default=0)

    retention_day_1_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))
    retention_day_7_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))
    retention_day_30_rate = models.DecimalField(max_digits=7, decimal_places=4, default=Decimal("0.0000"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_daily_user_cohort_retention"
        ordering = ["-cohort_date"]
        indexes = [
            models.Index(fields=["cohort_date"], name="analytics_cohort_date_idx"),
        ]

    def __str__(self) -> str:
        return f"User Cohort {self.cohort_date}"


class AnalyticsRefreshLog(models.Model):
    STATUS_RUNNING = "running"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
    ]

    trigger = models.CharField(max_length=32, default="manual")
    range_start = models.DateField()
    range_end = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RUNNING)
    rows_written = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "analytics_refresh_log"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status", "started_at"], name="analytics_refresh_status_idx"),
            models.Index(fields=["range_start", "range_end"], name="analytics_refresh_range_idx"),
        ]

    def __str__(self) -> str:
        return f"Analytics refresh {self.started_at} {self.status}"


class AnalyticsEvent(models.Model):
    EVENT_PAGE_VIEW = "page_view"
    EVENT_SESSION_START = "session_start"
    EVENT_VIDEO_VIEW = "video_view"
    EVENT_CHECKOUT_STARTED = "checkout_started"
    EVENT_PURCHASE_COMPLETED = "purchase_completed"
    EVENT_CHOICES = [
        (EVENT_PAGE_VIEW, "Page view"),
        (EVENT_SESSION_START, "Session start"),
        (EVENT_VIDEO_VIEW, "Video view"),
        (EVENT_CHECKOUT_STARTED, "Checkout started"),
        (EVENT_PURCHASE_COMPLETED, "Purchase completed"),
    ]

    event_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_name = models.CharField(max_length=32, choices=EVENT_CHOICES)
    occurred_at = models.DateTimeField()
    event_date = models.DateField(db_index=True)

    session_id = models.CharField(max_length=128, db_index=True)
    anonymous_id = models.CharField(max_length=128, blank=True, db_index=True)
    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    trainer_id = models.UUIDField(null=True, blank=True, db_index=True)
    order_id = models.UUIDField(null=True, blank=True, db_index=True)

    path = models.CharField(max_length=512, blank=True)
    referrer = models.CharField(max_length=1024, blank=True)
    utm_source = models.CharField(max_length=128, blank=True)
    utm_medium = models.CharField(max_length=128, blank=True)
    utm_campaign = models.CharField(max_length=128, blank=True)
    country_code = models.CharField(max_length=8, blank=True)
    device_type = models.CharField(max_length=32, blank=True)

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_event"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["event_date", "event_name"], name="analytics_event_date_name_idx"),
            models.Index(fields=["session_id", "occurred_at"], name="analytics_event_session_idx"),
            models.Index(fields=["utm_source", "utm_medium", "event_date"], name="analytics_event_utm_idx"),
            models.Index(fields=["trainer_id", "event_date"], name="analytics_event_trainer_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.event_name} {self.occurred_at}"


class DailyTrafficSlice(models.Model):
    date = models.DateField()
    path = models.CharField(max_length=512, blank=True)
    utm_source = models.CharField(max_length=128, blank=True)
    utm_medium = models.CharField(max_length=128, blank=True)
    utm_campaign = models.CharField(max_length=128, blank=True)
    trainer_id = models.UUIDField(null=True, blank=True)

    sessions = models.PositiveIntegerField(default=0)
    unique_users = models.PositiveIntegerField(default=0)
    page_views = models.PositiveIntegerField(default=0)
    video_views = models.PositiveIntegerField(default=0)
    checkout_starts = models.PositiveIntegerField(default=0)
    purchases = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_daily_traffic_slice"
        ordering = ["-date", "path"]
        unique_together = (("date", "path", "utm_source", "utm_medium", "utm_campaign", "trainer_id"),)
        indexes = [
            models.Index(fields=["date", "path"], name="analytics_slice_date_path_idx"),
            models.Index(fields=["date", "utm_source", "utm_medium"], name="analytics_slice_date_utm_idx"),
            models.Index(fields=["trainer_id", "date"], name="analytics_slice_trainer_idx"),
        ]

    def __str__(self) -> str:
        return f"Traffic slice {self.date} {self.path or '/'}"

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.products.models import Product, ProductItem
from apps.videos.models import Video


PRODUCT_TYPE_VIDEO = "video"
PRODUCT_TYPE_BUNDLE = "bundle"
PRODUCT_TYPES = (PRODUCT_TYPE_VIDEO, PRODUCT_TYPE_BUNDLE)

ACCESS_TYPE_ONE_TIME = "one_time"
ACCESS_TYPE_SUBSCRIPTION = "subscription"
ACCESS_TYPES = (ACCESS_TYPE_ONE_TIME, ACCESS_TYPE_SUBSCRIPTION)

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_ARCHIVED = "archived"
PRODUCT_STATUSES = (STATUS_DRAFT, STATUS_PUBLISHED, STATUS_ARCHIVED)

SUPPORTED_CURRENCIES = ("RUB", "USD", "EUR")
READY_VIDEO_STATUSES = ("ready", "published", "public")


@dataclass(frozen=True)
class ProductReadinessCheck:
    code: str
    title: str
    status: str
    message: str


def trainer_profile_for_user(user):
    if not user or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Authentication is required.")
    trainer_profile = getattr(user, "trainer_profile", None)
    if trainer_profile is None:
        raise PermissionDenied("Trainer profile is required to manage products.")
    return trainer_profile


def _to_decimal(value) -> Decimal:
    try:
        amount = Decimal(str(value if value is not None else "0"))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({"price_amount": "Invalid price amount."}) from exc
    return amount.quantize(Decimal("0.01"))


def _normalize_slug(value: str | None, *, title: str) -> str:
    base = value or title
    slug = slugify(str(base), allow_unicode=True).strip("-")
    if not slug:
        raise ValidationError({"slug": "Slug is required."})
    return slug[:160]


def _unique_preserving_order(values: Iterable) -> list:
    seen = set()
    result = []
    for value in values:
        key = str(value)
        if key in seen:
            raise ValidationError({"item_video_ids": "Duplicate video ids are not allowed."})
        seen.add(key)
        result.append(value)
    return result


class TrainerProductBuilderService:
    """Trainer-owned product builder policy.

    The database schema already has Product/ProductItem, so this service keeps v8.44
    migration-free and enforces lifecycle/ownership/publishing rules at the domain
    boundary.
    """

    def list_products(self, *, user):
        trainer = trainer_profile_for_user(user)
        return (
            Product.objects.filter(trainer=trainer, is_deleted=False)
            .prefetch_related("items", "items__video")
            .order_by("-updated_at", "-created_at")
        )

    def get_product(self, *, user, product_id):
        trainer = trainer_profile_for_user(user)
        try:
            return (
                Product.objects.filter(trainer=trainer, is_deleted=False)
                .prefetch_related("items", "items__video")
                .get(id=product_id)
            )
        except Product.DoesNotExist as exc:
            raise ValidationError({"detail": "Product not found."}) from exc

    def normalize_payload(self, payload: dict, *, instance: Product | None = None) -> dict:
        data = dict(payload)
        title = str(data.get("title") or getattr(instance, "title", "") or "").strip()
        if not title:
            raise ValidationError({"title": "Title is required."})

        data["title"] = title
        data["slug"] = _normalize_slug(data.get("slug") or getattr(instance, "slug", None), title=title)
        data["product_type"] = data.get("product_type") or getattr(instance, "product_type", PRODUCT_TYPE_VIDEO)
        data["access_type"] = data.get("access_type") or getattr(instance, "access_type", ACCESS_TYPE_ONE_TIME)
        data["status"] = data.get("status") or getattr(instance, "status", STATUS_DRAFT)
        data["currency"] = str(data.get("currency") or getattr(instance, "currency", "RUB")).upper()
        data["price_amount"] = _to_decimal(data.get("price_amount", getattr(instance, "price_amount", "0")))

        if data["product_type"] not in PRODUCT_TYPES:
            raise ValidationError({"product_type": f"Supported values: {', '.join(PRODUCT_TYPES)}."})
        if data["access_type"] not in ACCESS_TYPES:
            raise ValidationError({"access_type": f"Supported values: {', '.join(ACCESS_TYPES)}."})
        if data["status"] not in PRODUCT_STATUSES:
            raise ValidationError({"status": f"Supported values: {', '.join(PRODUCT_STATUSES)}."})
        if data["currency"] not in SUPPORTED_CURRENCIES:
            raise ValidationError({"currency": f"Supported values: {', '.join(SUPPORTED_CURRENCIES)}."})
        if data["price_amount"] < Decimal("0.00"):
            raise ValidationError({"price_amount": "Price cannot be negative."})

        return data

    def validate_slug_is_unique(self, *, trainer, slug: str, exclude: Product | None = None) -> None:
        qs = Product.objects.filter(trainer=trainer, slug=slug, is_deleted=False)
        if exclude is not None:
            qs = qs.exclude(id=exclude.id)
        if qs.exists():
            raise ValidationError({"slug": "Trainer already has a product with this slug."})

    def _owned_videos(self, *, trainer, item_video_ids: list) -> list[Video]:
        ids = _unique_preserving_order(item_video_ids)
        if not ids:
            return []

        videos_by_id = {
            str(video.id): video
            for video in Video.objects.filter(id__in=ids, trainer=trainer, is_deleted=False)
        }
        missing = [str(video_id) for video_id in ids if str(video_id) not in videos_by_id]
        if missing:
            raise ValidationError({"item_video_ids": f"Videos are not owned by trainer or do not exist: {', '.join(missing)}"})
        return [videos_by_id[str(video_id)] for video_id in ids]

    def sync_items(self, *, product: Product, videos: list[Video]) -> None:
        ProductItem.objects.filter(product=product).delete()
        ProductItem.objects.bulk_create(
            [ProductItem(product=product, video=video, position=index) for index, video in enumerate(videos)]
        )

    @transaction.atomic
    def create_product(self, *, user, payload: dict) -> Product:
        trainer = trainer_profile_for_user(user)
        item_video_ids = payload.pop("item_video_ids", []) or []
        data = self.normalize_payload(payload)
        self.validate_slug_is_unique(trainer=trainer, slug=data["slug"])
        if data["status"] == STATUS_PUBLISHED:
            raise ValidationError({"status": "Create product as draft, then publish explicitly."})

        videos = self._owned_videos(trainer=trainer, item_video_ids=item_video_ids)
        product = Product.objects.create(trainer=trainer, **data)
        self.sync_items(product=product, videos=videos)
        return self.get_product(user=user, product_id=product.id)

    @transaction.atomic
    def update_product(self, *, user, product_id, payload: dict, partial: bool = True) -> Product:
        product = self.get_product(user=user, product_id=product_id)
        if product.status == STATUS_ARCHIVED and payload.get("status") == STATUS_PUBLISHED:
            raise ValidationError({"status": "Archived product cannot be directly published."})

        item_video_ids_provided = "item_video_ids" in payload
        item_video_ids = payload.pop("item_video_ids", None)
        data = self.normalize_payload(payload, instance=product)
        self.validate_slug_is_unique(trainer=product.trainer, slug=data["slug"], exclude=product)

        for field, value in data.items():
            setattr(product, field, value)
        product.save(update_fields=[*data.keys(), "updated_at"])

        if item_video_ids_provided:
            videos = self._owned_videos(trainer=product.trainer, item_video_ids=item_video_ids or [])
            self.sync_items(product=product, videos=videos)

        return self.get_product(user=user, product_id=product.id)

    def readiness(self, *, product: Product) -> dict:
        items = list(product.items.all())
        checks: list[ProductReadinessCheck] = []

        def add(code: str, ok: bool, title: str, message: str):
            checks.append(ProductReadinessCheck(code=code, title=title, status="pass" if ok else "blocker", message=message))

        add("title", bool(product.title), "Title", "Product has a customer-facing title." if product.title else "Title is required.")
        add("slug", bool(product.slug), "Slug", "Product has a stable slug." if product.slug else "Slug is required.")
        add(
            "product_type",
            product.product_type in PRODUCT_TYPES,
            "Product type",
            f"Product type is {product.product_type}." if product.product_type in PRODUCT_TYPES else "Unsupported product type.",
        )
        add(
            "access_type",
            product.access_type in ACCESS_TYPES,
            "Access type",
            f"Access type is {product.access_type}." if product.access_type in ACCESS_TYPES else "Unsupported access type.",
        )
        add(
            "currency",
            product.currency in SUPPORTED_CURRENCIES,
            "Currency",
            f"Currency is {product.currency}." if product.currency in SUPPORTED_CURRENCIES else "Unsupported currency.",
        )
        add(
            "price",
            product.price_amount >= Decimal("0.00"),
            "Price",
            "Price is valid." if product.price_amount >= Decimal("0.00") else "Price cannot be negative.",
        )

        if product.product_type == PRODUCT_TYPE_VIDEO:
            add("items", len(items) == 1, "Single video", "Single video product has exactly one video." if len(items) == 1 else "Single video product requires exactly one video.")
        elif product.product_type == PRODUCT_TYPE_BUNDLE:
            add("items", len(items) >= 2, "Bundle items", "Bundle has at least two videos." if len(items) >= 2 else "Bundle requires at least two videos.")

        not_ready = [item.video_id for item in items if getattr(item.video, "status", None) not in READY_VIDEO_STATUSES]
        add(
            "video_readiness",
            not not_ready,
            "Video readiness",
            "All videos are ready for sale." if not not_ready else f"Not ready video ids: {', '.join(map(str, not_ready))}",
        )

        blockers = [check for check in checks if check.status != "pass"]
        return {
            "product_id": str(product.id),
            "status": "ready" if not blockers else "blocked",
            "blockers_count": len(blockers),
            "checks": [check.__dict__ for check in checks],
        }

    @transaction.atomic
    def publish_product(self, *, user, product_id) -> Product:
        product = self.get_product(user=user, product_id=product_id)
        readiness = self.readiness(product=product)
        if readiness["status"] != "ready":
            raise ValidationError({"detail": "Product is not ready to publish.", "readiness": readiness})
        product.status = STATUS_PUBLISHED
        product.save(update_fields=["status", "updated_at"])
        return self.get_product(user=user, product_id=product.id)

    @transaction.atomic
    def archive_product(self, *, user, product_id) -> Product:
        product = self.get_product(user=user, product_id=product_id)
        product.status = STATUS_ARCHIVED
        product.save(update_fields=["status", "updated_at"])
        return self.get_product(user=user, product_id=product.id)

    @transaction.atomic
    def soft_delete_product(self, *, user, product_id) -> None:
        product = self.get_product(user=user, product_id=product_id)
        if product.status == STATUS_PUBLISHED:
            raise ValidationError({"detail": "Published products must be archived before deletion."})
        product.is_deleted = True
        product.deleted_at = timezone.now()
        product.save(update_fields=["is_deleted", "deleted_at", "updated_at"])

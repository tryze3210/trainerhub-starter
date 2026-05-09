from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from django.db.models import QuerySet
from django.utils import timezone

from apps.orders.models import Order, OrderItem, OrderStatus, PurchasedItemType
from apps.payouts.models import BalanceEntry, TrainerWallet
from apps.products.models import Product, ProductItem
from apps.trainers.models import TrainerProfile
from apps.videos.models import Video

TWOPLACES = Decimal("0.01")


class TrainerAnalyticsAccessError(Exception):
    """Raised when the authenticated user does not have a trainer profile."""


@dataclass(frozen=True)
class _SourceRevenue:
    gross: Decimal = Decimal("0.00")
    debits: Decimal = Decimal("0.00")
    net: Decimal = Decimal("0.00")


def _money(value: Decimal | int | str | None) -> Decimal:
    return Decimal(value or "0.00").quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _money_str(value: Decimal | int | str | None) -> str:
    return str(_money(value))


def _safe_uuid(value: Any) -> UUID | None:
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _get_trainer_profile(user) -> TrainerProfile:
    profile = getattr(user, "trainer_profile", None)
    if not profile:
        raise TrainerAnalyticsAccessError("Trainer profile not found.")
    return profile


def _period(days: int) -> dict[str, Any]:
    until = timezone.now()
    since = until - timezone.timedelta(days=days)
    return {"days": days, "since": since, "until": until}


def _serialize_period(period: dict[str, Any]) -> dict[str, Any]:
    return {
        "days": period["days"],
        "since": period["since"].isoformat(),
        "until": period["until"].isoformat(),
    }


def _trainer_payload(profile: TrainerProfile) -> dict[str, Any]:
    return {
        "id": str(profile.id),
        "slug": profile.slug,
        "display_name": profile.display_name,
        "status": profile.status,
    }


def _video_views(video: Video) -> int:
    metadata = getattr(video.media_asset, "metadata_json", None) or {}
    for key in ("views_count", "views", "plays", "play_count"):
        try:
            value = int(metadata.get(key) or 0)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    return 0


def _entry_bucket(entry: BalanceEntry) -> tuple[str, str]:
    return (entry.source_type or "unknown", str(entry.source_id) if entry.source_id else "")


def _aggregate_revenue_by_source(wallet: TrainerWallet | None, *, since) -> dict[tuple[str, str], _SourceRevenue]:
    if not wallet:
        return {}

    gross: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    debits: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))

    entries = wallet.entries.filter(created_at__gte=since).order_by("created_at")
    for entry in entries:
        key = _entry_bucket(entry)
        amount = _money(entry.amount)
        if entry.direction == "credit":
            gross[key] += amount
        else:
            debits[key] += amount

    keys = set(gross) | set(debits)
    return {
        key: _SourceRevenue(
            gross=_money(gross[key]),
            debits=_money(debits[key]),
            net=_money(gross[key] - debits[key]),
        )
        for key in keys
    }


def _trainer_wallet(profile: TrainerProfile) -> TrainerWallet | None:
    return getattr(profile, "wallet", None)


def _order_items_for_period(*, since) -> QuerySet[OrderItem]:
    return (
        OrderItem.objects.select_related("order")
        .filter(order__status__in=[OrderStatus.PAID, OrderStatus.COMPLETED], order__created_at__gte=since)
        .order_by("-order__created_at", "-id")
    )


def _build_product_video_map(products: list[Product]) -> dict[str, set[str]]:
    product_ids = [product.id for product in products]
    mapping: dict[str, set[str]] = defaultdict(set)
    if not product_ids:
        return mapping
    for item in ProductItem.objects.filter(product_id__in=product_ids).select_related("video"):
        product_id = str(item.product_id)
        mapping[str(item.video_id)].add(product_id)
        if item.video and item.video.slug:
            mapping[item.video.slug].add(product_id)
    return mapping


def _purchase_indexes(
    *,
    videos: list[Video],
    products: list[Product],
    since,
) -> tuple[dict[str, int], dict[str, int], list[dict[str, Any]]]:
    video_lookup: dict[str, str] = {}
    product_lookup: dict[str, str] = {}
    for video in videos:
        video_lookup[str(video.id)] = str(video.id)
        video_lookup[video.slug] = str(video.id)
    for product in products:
        product_lookup[str(product.id)] = str(product.id)
        product_lookup[product.slug] = str(product.id)

    product_video_map = _build_product_video_map(products)
    video_purchases: dict[str, int] = defaultdict(int)
    product_purchases: dict[str, int] = defaultdict(int)
    sales: list[dict[str, Any]] = []

    for item in _order_items_for_period(since=since):
        raw_item_id = str(item.item_id)
        matched_video_id = video_lookup.get(raw_item_id)
        matched_product_id = product_lookup.get(raw_item_id)

        if item.item_type == PurchasedItemType.VIDEO and matched_video_id:
            video_purchases[matched_video_id] += item.quantity
        if matched_product_id:
            product_purchases[matched_product_id] += item.quantity
            for video_key, product_ids in product_video_map.items():
                canonical_video_id = video_lookup.get(video_key)
                if canonical_video_id and matched_product_id in product_ids:
                    video_purchases[canonical_video_id] += item.quantity

        if matched_video_id or matched_product_id:
            sales.append(
                {
                    "order_id": str(item.order_id),
                    "created_at": item.order.created_at.isoformat() if item.order.created_at else None,
                    "item_type": item.item_type,
                    "item_id": raw_item_id,
                    "title": item.title_snapshot,
                    "quantity": item.quantity,
                    "unit_price": _money_str(item.unit_price),
                    "total_price": _money_str(item.total_price),
                    "currency": item.order.currency,
                    "order_status": item.order.status,
                    "matched_content_type": "video" if matched_video_id else "product",
                    "matched_content_id": matched_video_id or matched_product_id,
                }
            )

    return dict(video_purchases), dict(product_purchases), sales


def _source_revenue_for_content(
    revenue_by_source: dict[tuple[str, str], _SourceRevenue],
    *,
    source_types: list[str],
    source_ids: list[str],
) -> _SourceRevenue:
    gross = Decimal("0.00")
    debits = Decimal("0.00")
    for source_type in source_types:
        for source_id in source_ids:
            source_uuid = _safe_uuid(source_id)
            source_id_variants = {source_id}
            if source_uuid:
                source_id_variants.add(str(source_uuid))
            for variant in source_id_variants:
                bucket = revenue_by_source.get((source_type, variant))
                if bucket:
                    gross += bucket.gross
                    debits += bucket.debits
    return _SourceRevenue(gross=_money(gross), debits=_money(debits), net=_money(gross - debits))


def _conversion_rate(purchases: int, views: int) -> str:
    if views <= 0:
        return "0.0000"
    return str((Decimal(purchases) / Decimal(views)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def _content_rows(profile: TrainerProfile, *, days: int, content_type: str, limit: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    period = _period(days)
    wallet = _trainer_wallet(profile)
    revenue_by_source = _aggregate_revenue_by_source(wallet, since=period["since"])

    videos = list(
        Video.objects.select_related("media_asset")
        .filter(trainer=profile, is_deleted=False)
        .order_by("-created_at")
    )
    products = list(Product.objects.filter(trainer=profile, is_deleted=False).order_by("-created_at"))
    video_purchases, product_purchases, sales = _purchase_indexes(videos=videos, products=products, since=period["since"])

    product_counts_by_video: dict[str, int] = defaultdict(int)
    for item in ProductItem.objects.filter(product__trainer=profile).values("video_id", "product_id"):
        product_counts_by_video[str(item["video_id"])] += 1

    rows: list[dict[str, Any]] = []
    if content_type in {"all", "video"}:
        for video in videos:
            views = _video_views(video)
            purchases = int(video_purchases.get(str(video.id), 0))
            revenue = _source_revenue_for_content(
                revenue_by_source,
                source_types=["video", "content_video"],
                source_ids=[str(video.id), video.slug],
            )
            rows.append(
                {
                    "content_type": "video",
                    "id": str(video.id),
                    "slug": video.slug,
                    "title": video.title,
                    "status": video.status,
                    "is_free": video.is_free,
                    "price_amount": None,
                    "currency": wallet.currency if wallet else "RUB",
                    "views_count": views,
                    "purchase_count": purchases,
                    "conversion_rate": _conversion_rate(purchases, views),
                    "gross_revenue": _money_str(revenue.gross),
                    "refund_amount": _money_str(revenue.debits),
                    "net_revenue": _money_str(revenue.net),
                    "product_count": product_counts_by_video.get(str(video.id), 0),
                    "created_at": video.created_at.isoformat() if video.created_at else None,
                    "updated_at": video.updated_at.isoformat() if video.updated_at else None,
                }
            )

    if content_type in {"all", "product"}:
        for product in products:
            purchases = int(product_purchases.get(str(product.id), 0))
            revenue = _source_revenue_for_content(
                revenue_by_source,
                source_types=["product", product.product_type, "bundle", "program", "subscription_plan"],
                source_ids=[str(product.id), product.slug],
            )
            items_count = ProductItem.objects.filter(product=product).count()
            rows.append(
                {
                    "content_type": "product",
                    "id": str(product.id),
                    "slug": product.slug,
                    "title": product.title,
                    "status": product.status,
                    "product_type": product.product_type,
                    "access_type": product.access_type,
                    "is_free": product.price_amount == 0,
                    "price_amount": _money_str(product.price_amount),
                    "currency": product.currency,
                    "views_count": 0,
                    "purchase_count": purchases,
                    "conversion_rate": "0.0000",
                    "gross_revenue": _money_str(revenue.gross),
                    "refund_amount": _money_str(revenue.debits),
                    "net_revenue": _money_str(revenue.net),
                    "product_count": items_count,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                    "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                }
            )

    rows.sort(key=lambda row: (Decimal(row["net_revenue"]), row["purchase_count"], row["created_at"] or ""), reverse=True)
    limited_rows = rows[:limit]

    overview = {
        "period": _serialize_period(period),
        "trainer": _trainer_payload(profile),
        "currency": wallet.currency if wallet else "RUB",
        "counts": {
            "videos": len(videos),
            "products": len(products),
            "published_videos": sum(1 for video in videos if video.status in {"published", "active", "verified"}),
            "published_products": sum(1 for product in products if product.status in {"published", "active"}),
            "free_videos": sum(1 for video in videos if video.is_free),
            "paid_products": sum(1 for product in products if Decimal(product.price_amount or 0) > 0),
        },
        "sales": {
            "matched_sales": len(sales),
            "purchased_units": sum(int(sale["quantity"]) for sale in sales),
            "gross_order_sales": _money_str(sum((Decimal(sale["total_price"]) for sale in sales), Decimal("0.00"))),
        },
        "performance": {
            "gross_revenue": _money_str(sum((Decimal(row["gross_revenue"]) for row in rows), Decimal("0.00"))),
            "refund_amount": _money_str(sum((Decimal(row["refund_amount"]) for row in rows), Decimal("0.00"))),
            "net_revenue": _money_str(sum((Decimal(row["net_revenue"]) for row in rows), Decimal("0.00"))),
            "total_views": sum(int(row["views_count"]) for row in rows),
            "total_purchases": sum(int(row["purchase_count"]) for row in rows),
        },
        "top_content": limited_rows[:5],
        "notes": [
            "Views are read from media asset metadata when available.",
            "Revenue is based on payout ledger source_type/source_id mappings.",
            "Order item sales are matched by UUID or slug snapshots to avoid cross-trainer leakage.",
        ],
    }
    return overview, limited_rows, sales[:limit]


def build_trainer_content_analytics_overview(*, user, days: int = 30) -> dict[str, Any]:
    profile = _get_trainer_profile(user)
    overview, _, _ = _content_rows(profile, days=days, content_type="all", limit=20)
    return overview


def list_trainer_content_performance(*, user, days: int = 30, content_type: str = "all", limit: int = 50) -> dict[str, Any]:
    profile = _get_trainer_profile(user)
    overview, rows, _ = _content_rows(profile, days=days, content_type=content_type, limit=limit)
    return {
        "period": overview["period"],
        "trainer": overview["trainer"],
        "currency": overview["currency"],
        "content_type": content_type,
        "limit": limit,
        "count": len(rows),
        "summary": overview["performance"],
        "results": rows,
    }


def list_trainer_sales_analytics(*, user, days: int = 30, limit: int = 50) -> dict[str, Any]:
    profile = _get_trainer_profile(user)
    overview, _, sales = _content_rows(profile, days=days, content_type="all", limit=limit)
    return {
        "period": overview["period"],
        "trainer": overview["trainer"],
        "currency": overview["currency"],
        "limit": limit,
        "count": len(sales),
        "summary": overview["sales"],
        "results": sales,
    }

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class ProviderExportResult:
    provider_batch_reference: str
    items: list[dict]
    raw_payload: dict


@dataclass(slots=True)
class ProviderEvent:
    provider: str
    event_id: str
    event_type: str
    provider_reference: str
    status: str
    payload: dict


class SettlementProviderGateway(Protocol):
    provider_code: str

    def export_payout_batch(self, *, batch, items: list) -> ProviderExportResult:
        ...

    def parse_webhook(self, *, headers: dict, payload: dict) -> ProviderEvent:
        ...

    def fetch_transactions(self, *, date_from, date_to) -> list[dict]:
        ...


class ManualSettlementGateway:
    provider_code = "manual"

    def export_payout_batch(self, *, batch, items: list) -> ProviderExportResult:
        exported_items = [
            {
                "local_payout_item_id": str(item.id),
                "provider_reference": f"manual-item-{item.id}",
                "amount": str(item.amount),
                "currency": getattr(item, "currency", "RUB"),
            }
            for item in items
        ]
        return ProviderExportResult(
            provider_batch_reference=f"manual-batch-{batch.id}",
            items=exported_items,
            raw_payload={"mode": "manual", "items_count": len(exported_items)},
        )

    def parse_webhook(self, *, headers: dict, payload: dict) -> ProviderEvent:
        return ProviderEvent(
            provider=self.provider_code,
            event_id=payload["event_id"],
            event_type=payload["event_type"],
            provider_reference=payload["provider_reference"],
            status=payload["status"],
            payload=payload,
        )

    def fetch_transactions(self, *, date_from, date_to) -> list[dict]:
        return []

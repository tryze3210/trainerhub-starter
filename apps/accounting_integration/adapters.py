from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class DeliveryResult:
    is_success: bool
    external_reference: str = ""
    response_payload: dict[str, Any] | None = None
    error_message: str = ""


class BaseAccountingAdapter:
    adapter_key = "base"

    def build_export_payload(self, export_run) -> dict[str, Any]:
        raise NotImplementedError

    def render_file(self, export_run) -> tuple[str, bytes, str]:
        raise NotImplementedError

    def deliver(self, export_run) -> DeliveryResult:
        raise NotImplementedError


class ManualJSONAccountingAdapter(BaseAccountingAdapter):
    adapter_key = "manual_json"

    def build_export_payload(self, export_run) -> dict[str, Any]:
        batch = export_run.journal_batch
        return {
            "system": export_run.system.code,
            "period_id": export_run.period_id,
            "batch_number": batch.batch_number,
            "currency": batch.currency,
            "entries": [
                {
                    "entry_number": entry.entry_number,
                    "date": entry.entry_date.isoformat(),
                    "reference": entry.reference,
                    "description": entry.description,
                    "lines": [
                        {
                            "line_number": line.line_number,
                            "account_code": line.account.code,
                            "debit_amount": str(line.debit_amount),
                            "credit_amount": str(line.credit_amount),
                            "currency": line.currency,
                            "dimensions": line.dimensions,
                        }
                        for line in entry.lines.all()
                    ],
                }
                for entry in batch.entries.all().prefetch_related("lines__account")
            ],
        }

    def render_file(self, export_run) -> tuple[str, bytes, str]:
        import hashlib
        import json

        payload = self.build_export_payload(export_run)
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        checksum = hashlib.sha256(raw).hexdigest()
        filename = f"gl_export_{export_run.run_number}.json"
        return filename, raw, checksum

    def deliver(self, export_run) -> DeliveryResult:
        return DeliveryResult(
            is_success=True,
            external_reference=export_run.run_number,
            response_payload={"mode": "manual", "status": "accepted"},
        )


class AccountingAdapterRegistry:
    def __init__(self):
        self._adapters = {
            ManualJSONAccountingAdapter.adapter_key: ManualJSONAccountingAdapter(),
        }

    def get(self, adapter_key: str) -> BaseAccountingAdapter:
        return self._adapters[adapter_key]


adapter_registry = AccountingAdapterRegistry()

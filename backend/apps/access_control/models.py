from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    code: str
    reason: str
    required_capability: str | None = None
    feature_key: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FeatureGateResult:
    key: str
    enabled: bool
    reason: str
    required_role: str | None = None
    required_onboarding_steps: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ObjectPolicyDecision:
    allowed: bool
    code: str
    reason: str
    object_type: str
    object_id: str
    action: str
    tenant_id: str | None = None
    owner_account_id: str | None = None
    actor_account_id: str | None = None
    actor_role: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.db import models

from apps.common.models import TimeStampedModel


class Tenant(TimeStampedModel):
    code = models.CharField(max_length=64, unique=True)
    kind = models.CharField(max_length=32, default='trainer_space')
    name = models.CharField(max_length=255)
    owner_account_id = models.CharField(max_length=64)
    status = models.CharField(max_length=32, default='active')
    settings = models.JSONField(default=dict)

    class Meta:
        db_table = 'tenancy_tenant'


class TenantMembership(TimeStampedModel):
    tenant_id = models.CharField(max_length=64)
    account_id = models.CharField(max_length=64)
    role = models.CharField(max_length=32)
    status = models.CharField(max_length=32, default='active')
    permissions = models.JSONField(default=list)

    class Meta:
        db_table = 'tenancy_membership'
        unique_together = ('tenant_id', 'account_id', 'role')


@dataclass(slots=True)
class TenantContext:
    active_tenant: dict[str, Any]
    memberships: list[dict[str, Any]]
    accessible_tenant_ids: list[str] = field(default_factory=list)

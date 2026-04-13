from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.onboarding import selectors
from apps.onboarding.models import OnboardingStepState


def list_steps(*, user) -> list[dict[str, Any]]:
    return selectors.list_steps(user=user)


def complete_step(*, user, code: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    step = selectors.get_step(code)
    if not step:
        raise ValueError('Unknown onboarding step')
    state, _ = OnboardingStepState.objects.update_or_create(
        user=user,
        step_code=code,
        defaults={
            'is_completed': True,
            'completed_at': timezone.now(),
            'payload': payload or {},
        },
    )
    return {
        'step_code': state.step_code,
        'status': 'completed',
        'payload': state.payload,
    }


def get_status(*, user) -> dict[str, Any]:
    return selectors.build_status(user=user)

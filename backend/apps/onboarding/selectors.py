from __future__ import annotations

from typing import Any

from apps.onboarding.models import OnboardingStepState

ONBOARDING_STEPS = [
    {
        'code': 'account_basics',
        'title': 'Complete account basics',
        'description': 'Set display name, locale and preferred language.',
        'role_scope': 'all',
        'sort_order': 10,
    },
    {
        'code': 'favorites_setup',
        'title': 'Choose favorite categories',
        'description': 'Personalize recommendations and catalog ranking.',
        'role_scope': 'user',
        'sort_order': 20,
    },
    {
        'code': 'trainer_profile',
        'title': 'Create trainer profile',
        'description': 'Prepare public trainer identity and positioning.',
        'role_scope': 'trainer',
        'sort_order': 30,
    },
    {
        'code': 'payout_setup',
        'title': 'Configure payout destination',
        'description': 'Required before trainer earnings can be withdrawn.',
        'role_scope': 'trainer',
        'sort_order': 40,
    },
    {
        'code': 'first_publish',
        'title': 'Submit first content item',
        'description': 'Send a draft into moderation to unlock storefront visibility.',
        'role_scope': 'trainer',
        'sort_order': 50,
    },
]


def list_steps(*, user) -> list[dict[str, Any]]:
    completed_map = {
        row['step_code']: row['is_completed']
        for row in OnboardingStepState.objects.filter(user=user).values('step_code', 'is_completed')
    }
    return [
        {
            **item,
            'is_completed': completed_map.get(item['code'], False),
        }
        for item in sorted(ONBOARDING_STEPS, key=lambda x: x['sort_order'])
    ]


def get_step(code: str) -> dict[str, Any] | None:
    for item in ONBOARDING_STEPS:
        if item['code'] == code:
            return dict(item)
    return None


def build_status(*, user) -> dict[str, Any]:
    steps = list_steps(user=user)
    completed = len([step for step in steps if step['is_completed']])
    total = len(steps)
    return {
        'steps': steps,
        'summary': {
            'completed_steps': completed,
            'total_steps': total,
            'completion_percent': int((completed / total) * 100) if total else 0,
            'next_step': next((step['code'] for step in steps if not step['is_completed']), None),
        },
    }

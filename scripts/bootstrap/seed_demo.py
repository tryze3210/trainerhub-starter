from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from django.contrib.auth import get_user_model

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings
from apps.onboarding.models import OnboardingStepState

User = get_user_model()


def main() -> None:
    email = 'trainer@example.com'
    password = 'trainer12345'
    full_name = 'Anna Trainer'
    user, created = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': full_name},
    )
    if created:
        user.set_password(password)
        user.save(update_fields=['password'])
    AccountProfile.objects.get_or_create(user=user, defaults={'full_name': full_name, 'display_name': 'Anna'})
    AccountSettings.objects.get_or_create(user=user)
    AccountRoleAssignment.objects.get_or_create(user=user, role='user', defaults={'is_active': False})
    AccountRoleAssignment.objects.get_or_create(user=user, role='trainer', defaults={'is_active': True})
    OnboardingStepState.objects.get_or_create(user=user, step_code='account_basics', defaults={'is_completed': True})
    OnboardingStepState.objects.get_or_create(user=user, step_code='trainer_profile', defaults={'is_completed': True})
    print('Seeded demo user: trainer@example.com / trainer12345')


if __name__ == '__main__':
    main()

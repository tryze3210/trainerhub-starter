from __future__ import annotations

import os
import sys
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

from apps.accounts.models import AccountProfile, AccountRoleAssignment, AccountSettings
from apps.onboarding.models import OnboardingStepState
from scripts.bootstrap.seed_demo import build_demo_seed_payload

User = get_user_model()


def _assert_demo_seed_allowed() -> None:
    if getattr(settings, 'IS_PRODUCTION', False) and os.getenv('ALLOW_DEMO_SEED') != '1':
        raise RuntimeError('Demo seed is disabled in production. Set ALLOW_DEMO_SEED=1 only for an intentional smoke dataset.')


def _upsert_user(*, email: str, password: str, display_name: str):
    user, created = User.objects.get_or_create(
        email=email,
        defaults={'first_name': display_name},
    )
    if created:
        user.set_password(password)
        user.save(update_fields=['password'])
    return user


def _seed_accounts(payload: dict) -> dict[str, object]:
    users = {}
    for account in payload['accounts']:
        user = _upsert_user(
            email=account['email'],
            password=account['password'],
            display_name=account['display_name'],
        )
        users[account['key']] = user
        first_name = account['display_name'].split()[0]
        AccountProfile.objects.get_or_create(
            user=user,
            defaults={'full_name': account['display_name'], 'display_name': first_name},
        )
        AccountSettings.objects.get_or_create(user=user)
        for role in account['roles']:
            AccountRoleAssignment.objects.get_or_create(user=user, role=role, defaults={'is_active': True})
        if 'user' not in account['roles']:
            AccountRoleAssignment.objects.get_or_create(user=user, role='user', defaults={'is_active': False})
    return users


def _seed_onboarding(trainer_user) -> None:
    AccountSettings.objects.get_or_create(user=trainer_user)
    OnboardingStepState.objects.get_or_create(
        user=trainer_user,
        step_code='account_basics',
        defaults={'is_completed': True},
    )
    OnboardingStepState.objects.get_or_create(
        user=trainer_user,
        step_code='trainer_profile',
        defaults={'is_completed': True},
    )


def _seed_catalog(payload: dict, users: dict[str, object]) -> dict[str, str]:
    from apps.content.models import PublishedBundle, PublishedBundleItem, PublishedLesson, PublishedProgram, PublishedVideo
    from apps.trainer_profiles.models import TrainerPublicProfile
    from apps.trainers.models import TrainerProfile

    trainer_user = users['trainer_anna']
    trainer_config = payload['trainers'][0]
    TrainerProfile.objects.update_or_create(
        user=trainer_user,
        defaults={
            'slug': trainer_config['slug'],
            'display_name': trainer_config['display_name'],
            'headline': trainer_config['headline'],
            'bio': 'Demo trainer for launch smoke scenarios.',
            'status': 'approved',
            'is_public': True,
        },
    )
    public_profile, _ = TrainerPublicProfile.objects.update_or_create(
        user=trainer_user,
        defaults={
            'slug': trainer_config['slug'],
            'display_name': trainer_config['display_name'],
            'headline': trainer_config['headline'],
            'bio': 'Demo trainer for marketplace and billing scenarios.',
            'is_public': True,
        },
    )

    catalog_ids: dict[str, str] = {}
    for video in payload['catalog']['videos']:
        row, _ = PublishedVideo.objects.update_or_create(
            slug=video['slug'],
            defaults={
                'trainer_profile': public_profile,
                'source_draft_id': uuid.uuid5(uuid.NAMESPACE_URL, f"demo-video:{video['slug']}"),
                'title': video['title'],
                'description': 'Demo paid video.',
                'price_amount': Decimal(video['price_amount']),
                'currency': video['currency'],
                'duration_minutes': video['duration_minutes'],
                'is_active': True,
            },
        )
        catalog_ids[video['slug']] = str(row.id)

    for program in payload['catalog']['programs']:
        row, _ = PublishedProgram.objects.update_or_create(
            slug=program['slug'],
            defaults={
                'trainer_profile': public_profile,
                'source_draft_id': uuid.uuid5(uuid.NAMESPACE_URL, f"demo-program:{program['slug']}"),
                'title': program['title'],
                'description': 'Demo course with active entitlement.',
                'price_amount': Decimal(program['price_amount']),
                'currency': program['currency'],
                'duration_minutes': 120,
                'is_active': True,
            },
        )
        catalog_ids[program['slug']] = str(row.id)
        for lesson in program['lessons']:
            PublishedLesson.objects.update_or_create(
                slug=lesson['slug'],
                defaults={
                    'program': row,
                    'source_draft_id': uuid.uuid5(uuid.NAMESPACE_URL, f"demo-lesson:{lesson['slug']}"),
                    'title': lesson['title'],
                    'description': 'Demo lesson.',
                    'position': lesson['position'],
                    'duration_minutes': 30,
                },
            )

    for bundle in payload['catalog']['bundles']:
        row, _ = PublishedBundle.objects.update_or_create(
            slug=bundle['slug'],
            defaults={
                'trainer_profile': public_profile,
                'source_draft_id': uuid.uuid5(uuid.NAMESPACE_URL, f"demo-bundle:{bundle['slug']}"),
                'title': bundle['title'],
                'description': 'Demo bundle for refunded order scenario.',
                'price_amount': Decimal(bundle['price_amount']),
                'currency': bundle['currency'],
                'duration_minutes': 180,
                'is_active': True,
            },
        )
        catalog_ids[bundle['slug']] = str(row.id)
        for position, target_slug in enumerate(bundle['items'], start=1):
            item_type = PublishedBundleItem.ItemType.PROGRAM if target_slug == 'mobility-foundations' else PublishedBundleItem.ItemType.VIDEO
            PublishedBundleItem.objects.update_or_create(
                bundle=row,
                target_slug=target_slug,
                defaults={'item_type': item_type, 'position': position},
            )

    return catalog_ids


def _seed_commerce(payload: dict, users: dict[str, object], catalog_ids: dict[str, str]) -> None:
    from apps.entitlements.models import Entitlement, EntitlementSourceType, EntitlementStatus, EntitlementTargetType
    from apps.orders.models import Order, OrderItem, OrderStatus, OrderType, PurchasedItemType
    from apps.payments.models import Payment, PaymentProvider, PaymentStatus
    from apps.subscriptions.models import Subscription, SubscriptionPlan

    status_map = {
        'paid': OrderStatus.PAID,
        'failed': OrderStatus.FAILED,
        'refunded': OrderStatus.REFUNDED,
    }
    payment_status_map = {
        'succeeded': PaymentStatus.SUCCEEDED,
        'failed': PaymentStatus.FAILED,
        'refunded': PaymentStatus.REFUNDED,
    }
    item_type_map = {
        'program': PurchasedItemType.PROGRAM,
        'video': PurchasedItemType.VIDEO,
        'bundle': PurchasedItemType.BUNDLE,
    }
    for order_config in payload['commerce']['orders']:
        user = users[order_config['user']]
        amount = Decimal(order_config['total_amount'])
        order, _ = Order.objects.update_or_create(
            external_checkout_id=f"demo:{order_config['key']}",
            defaults={
                'user': user,
                'order_type': OrderType.ONE_TIME,
                'status': status_map[order_config['status']],
                'currency': 'RUB',
                'total_amount': amount,
                'paid_at': timezone.now() if order_config['status'] in {'paid', 'refunded'} else None,
            },
        )
        OrderItem.objects.update_or_create(
            order=order,
            item_id=catalog_ids[order_config['item_slug']],
            defaults={
                'item_type': item_type_map[order_config['item_type']],
                'title_snapshot': order_config['item_slug'],
                'quantity': 1,
                'unit_price': amount,
                'total_price': amount,
                'metadata': {'demo_scenario': order_config['key'], 'slug': order_config['item_slug']},
            },
        )
        Payment.objects.update_or_create(
            external_payment_id=f"demo:{order_config['key']}",
            defaults={
                'order': order,
                'provider': PaymentProvider.MOCK,
                'status': payment_status_map[order_config['payment_status']],
                'amount': amount,
                'currency': 'RUB',
                'provider_payload': {'demo_scenario': order_config['key']},
                'confirmed_at': timezone.now() if order_config['payment_status'] == 'succeeded' else None,
            },
        )

    entitlement_config = payload['commerce']['entitlements'][0]
    Entitlement.objects.update_or_create(
        user=users[entitlement_config['user']],
        target_type=EntitlementTargetType.PROGRAM,
        target_id=catalog_ids[entitlement_config['target_slug']],
        defaults={
            'source_type': EntitlementSourceType.ADMIN_GRANT,
            'status': EntitlementStatus.ACTIVE,
            'starts_at': timezone.now(),
            'metadata': {'demo_scenario': entitlement_config['key'], 'slug': entitlement_config['target_slug']},
        },
    )

    subscription_config = payload['commerce']['subscriptions'][0]
    plan, _ = SubscriptionPlan.objects.update_or_create(
        code=subscription_config['plan_code'],
        defaults={'trainer_id': 'trainer_anna', 'title': 'Demo Monthly', 'price': Decimal('2900.00'), 'currency': 'RUB'},
    )
    Subscription.objects.update_or_create(
        user=users[subscription_config['user']],
        plan=plan,
        defaults={
            'status': subscription_config['status'],
            'starts_at': timezone.now() - timedelta(days=33),
            'ends_at': timezone.now() - timedelta(days=subscription_config['ends_days_ago']),
            'auto_renew': False,
        },
    )


def _seed_payout(payload: dict, users: dict[str, object]) -> None:
    from apps.payouts.models import BalanceEntry, PayoutRequest, TrainerWallet
    from apps.trainers.models import TrainerProfile

    payout_config = payload['finance']['payouts'][0]
    trainer = TrainerProfile.objects.get(user=users[payout_config['trainer']])
    wallet, _ = TrainerWallet.objects.update_or_create(
        trainer=trainer,
        defaults={
            'currency': payout_config['currency'],
            'available_amount': Decimal(payout_config['available_amount']),
            'pending_amount': Decimal('0.00'),
            'locked_amount': Decimal('0.00'),
        },
    )
    source_id = uuid.uuid5(uuid.NAMESPACE_URL, 'demo:payout-ready-sale')
    BalanceEntry.objects.update_or_create(
        wallet=wallet,
        source_type='payment',
        source_id=source_id,
        defaults={
            'entry_type': BalanceEntry.EntryType.SALE_CREDIT,
            'direction': 'credit',
            'amount': Decimal(payout_config['available_amount']),
            'currency': payout_config['currency'],
            'status': 'available',
        },
    )
    PayoutRequest.objects.update_or_create(
        trainer=trainer,
        wallet=wallet,
        amount=Decimal(payout_config['payout_amount']),
        defaults={
            'currency': payout_config['currency'],
            'status': payout_config['status'],
            'destination_json': {'destination_masked': '**** 4242', 'demo_scenario': payout_config['key']},
        },
    )


def _run_optional_seed(label: str, fn, *args) -> None:
    try:
        fn(*args)
    except Exception as exc:
        print(f"Skipped {label}: {exc}")


def main() -> None:
    _assert_demo_seed_allowed()
    payload = build_demo_seed_payload()
    users = _seed_accounts(payload)
    _seed_onboarding(users['trainer_anna'])
    catalog_ids: dict[str, str] = {}
    _run_optional_seed('catalog demo products', lambda: catalog_ids.update(_seed_catalog(payload, users)))
    if catalog_ids:
        _run_optional_seed('commerce demo scenarios', _seed_commerce, payload, users, catalog_ids)
    _run_optional_seed('payout demo scenario', _seed_payout, payload, users)
    print('Seeded demo users: trainer@example.com / trainer12345, student@example.com / student12345')


if __name__ == '__main__':
    main()

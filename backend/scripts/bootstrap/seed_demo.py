from __future__ import annotations

import os

from django.conf import settings

DEMO_VERSION = 'v117'


def _assert_demo_seed_allowed() -> None:
    if getattr(settings, 'IS_PRODUCTION', False) and os.getenv('ALLOW_DEMO_SEED') != '1':
        raise RuntimeError('Demo seed is disabled in production. Set ALLOW_DEMO_SEED=1 only for an intentional smoke dataset.')


def build_demo_seed_payload() -> dict:
    return {
        'version': DEMO_VERSION,
        'accounts': [
            {
                'key': 'trainer_anna',
                'email': 'trainer@example.com',
                'password': 'trainer12345',
                'roles': ['trainer'],
                'display_name': 'Anna Trainer',
            },
            {
                'key': 'student_mila',
                'email': 'student@example.com',
                'password': 'student12345',
                'roles': ['user'],
                'display_name': 'Mila Student',
            },
        ],
        'trainers': [
            {
                'key': 'trainer_anna',
                'slug': 'anna-trainer-demo',
                'display_name': 'Anna Trainer',
                'headline': 'Strength and mobility coach',
                'products': ['mobility-foundations', 'kettlebell-basics', 'starter-bundle'],
            },
        ],
        'catalog': {
            'videos': [
                {
                    'slug': 'kettlebell-basics',
                    'title': 'Kettlebell Basics',
                    'price_amount': '1900.00',
                    'currency': 'RUB',
                    'duration_minutes': 42,
                },
            ],
            'programs': [
                {
                    'slug': 'mobility-foundations',
                    'title': 'Mobility Foundations',
                    'price_amount': '4900.00',
                    'currency': 'RUB',
                    'lessons': [
                        {'slug': 'mobility-day-1', 'title': 'Assessment and breath', 'position': 1},
                        {'slug': 'mobility-day-2', 'title': 'Hips and spine flow', 'position': 2},
                    ],
                },
            ],
            'bundles': [
                {
                    'slug': 'starter-bundle',
                    'title': 'Starter Bundle',
                    'price_amount': '5900.00',
                    'currency': 'RUB',
                    'items': ['mobility-foundations', 'kettlebell-basics'],
                },
            ],
        },
        'commerce': {
            'orders': [
                {
                    'key': 'student_active_course_order',
                    'user': 'student_mila',
                    'status': 'paid',
                    'item_type': 'program',
                    'item_slug': 'mobility-foundations',
                    'total_amount': '4900.00',
                    'payment_status': 'succeeded',
                },
                {
                    'key': 'student_failed_payment_order',
                    'user': 'student_mila',
                    'status': 'failed',
                    'item_type': 'video',
                    'item_slug': 'kettlebell-basics',
                    'total_amount': '1900.00',
                    'payment_status': 'failed',
                },
                {
                    'key': 'student_refunded_order',
                    'user': 'student_mila',
                    'status': 'refunded',
                    'item_type': 'bundle',
                    'item_slug': 'starter-bundle',
                    'total_amount': '5900.00',
                    'payment_status': 'refunded',
                },
            ],
            'entitlements': [
                {
                    'key': 'student_active_course',
                    'user': 'student_mila',
                    'target_type': 'program',
                    'target_slug': 'mobility-foundations',
                    'status': 'active',
                },
            ],
            'subscriptions': [
                {
                    'key': 'student_expired_subscription',
                    'user': 'student_mila',
                    'plan_code': 'demo-monthly',
                    'status': 'expired',
                    'ends_days_ago': 3,
                },
            ],
        },
        'finance': {
            'payouts': [
                {
                    'key': 'trainer_payout_ready',
                    'trainer': 'trainer_anna',
                    'status': 'approved',
                    'available_amount': '4200.00',
                    'payout_amount': '3000.00',
                    'currency': 'RUB',
                },
            ],
        },
        'scenarios': [
            'trainer_with_products',
            'student_with_active_course',
            'failed_payment',
            'refunded_order',
            'payout_ready',
            'subscription_expired',
        ],
        'commands': [
            'cd backend && python manage.py migrate',
            'python scripts/bootstrap/seed_demo.py',
        ],
    }

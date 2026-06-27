from scripts.bootstrap.seed_demo import build_demo_seed_payload


def test_demo_seed_payload_declares_launch_scenarios():
    payload = build_demo_seed_payload()

    assert payload['version'] == 'v117'
    assert set(payload['scenarios']) == {
        'trainer_with_products',
        'student_with_active_course',
        'failed_payment',
        'refunded_order',
        'payout_ready',
        'subscription_expired',
    }


def test_demo_seed_payload_has_business_fixture_sections():
    payload = build_demo_seed_payload()

    assert {account['key'] for account in payload['accounts']} == {'trainer_anna', 'student_mila'}
    assert payload['trainers'][0]['products'] == [
        'mobility-foundations',
        'kettlebell-basics',
        'starter-bundle',
    ]
    assert {order['key'] for order in payload['commerce']['orders']} == {
        'student_active_course_order',
        'student_failed_payment_order',
        'student_refunded_order',
    }
    assert payload['commerce']['entitlements'][0]['status'] == 'active'
    assert payload['commerce']['subscriptions'][0]['status'] == 'expired'
    assert payload['finance']['payouts'][0]['status'] == 'approved'

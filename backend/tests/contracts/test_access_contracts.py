from apps.access_control import policies


def test_access_snapshot_contract(access_snapshot):
    assert access_snapshot['role'] == 'trainer'
    assert 'features' in access_snapshot
    assert access_snapshot['features']['trainer_cms'] is True


def test_policy_decision_contract(request_context):
    decision = policies.PolicyService().check_feature(
        request=request_context,
        feature_code='trainer_cms',
    )
    assert 'allowed' in decision
    assert 'reason' in decision

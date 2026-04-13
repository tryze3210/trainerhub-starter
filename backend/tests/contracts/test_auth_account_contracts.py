from apps.authn import services as authn_services
from apps.accounts import services as account_services


def test_register_contract():
    payload = authn_services.register_user(
        email='new@example.com',
        password='strong-password',
        full_name='New User',
    )
    assert 'user' in payload
    assert payload['user']['email'] == 'new@example.com'


def test_profile_contract(request_context):
    payload = account_services.get_profile(request=request_context)
    assert 'display_name' in payload

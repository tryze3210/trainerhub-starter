from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APIClient


User = get_user_model()


def test_register_login_me_flow(db):
    client = APIClient()
    register_response = client.post('/api/v1/auth/register/', {
        'email': 'owner@example.com',
        'password': 'strong-pass-123',
        'full_name': 'Owner Example',
    }, format='json')
    assert register_response.status_code == 201
    assert User.objects.filter(email='owner@example.com').exists()

    login_response = client.post('/api/v1/auth/login/', {
        'email': 'owner@example.com',
        'password': 'strong-pass-123',
    }, format='json')
    assert login_response.status_code == 200
    assert 'access_token' not in login_response.json()
    assert 'refresh_token' not in login_response.json()
    assert settings.AUTH_ACCESS_COOKIE_NAME in login_response.cookies
    assert settings.AUTH_REFRESH_COOKIE_NAME in login_response.cookies

    me_response = client.get('/api/v1/auth/me/')
    assert me_response.status_code == 200
    assert me_response.json()['user']['email'] == 'owner@example.com'

    refresh_response = client.post('/api/v1/auth/refresh/', {}, format='json')
    assert refresh_response.status_code == 200
    assert refresh_response.json() == {'status': 'refreshed'}
    assert settings.AUTH_ACCESS_COOKIE_NAME in refresh_response.cookies
    assert settings.AUTH_REFRESH_COOKIE_NAME in refresh_response.cookies

    logout_response = client.post('/api/v1/auth/logout/', {}, format='json')
    assert logout_response.status_code == 200
    assert logout_response.cookies[settings.AUTH_ACCESS_COOKIE_NAME].value == ''
    assert logout_response.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value == ''

    me_after_logout_response = client.get('/api/v1/auth/me/')
    assert me_after_logout_response.status_code in {401, 403}


def test_cookie_auth_unsafe_requests_require_csrf(db):
    User.objects.create_user(email='csrf-owner@example.com', password='strong-pass-123')
    client = APIClient(enforce_csrf_checks=True)

    login_response = client.post('/api/v1/auth/login/', {
        'email': 'csrf-owner@example.com',
        'password': 'strong-pass-123',
    }, format='json')
    assert login_response.status_code == 200
    assert settings.CSRF_COOKIE_NAME in login_response.cookies

    me_response = client.get('/api/v1/auth/me/')
    assert me_response.status_code == 200

    refresh_without_csrf = client.post('/api/v1/auth/refresh/', {}, format='json')
    assert refresh_without_csrf.status_code == 403

    csrf_token = login_response.cookies[settings.CSRF_COOKIE_NAME].value
    refresh_with_csrf = client.post(
        '/api/v1/auth/refresh/',
        {},
        HTTP_X_CSRFTOKEN=csrf_token,
        format='json',
    )
    assert refresh_with_csrf.status_code == 200

    logout_without_csrf = client.post('/api/v1/auth/logout/', {}, format='json')
    assert logout_without_csrf.status_code == 403

    logout_with_csrf = client.post(
        '/api/v1/auth/logout/',
        {},
        HTTP_X_CSRFTOKEN=client.cookies[settings.CSRF_COOKIE_NAME].value,
        format='json',
    )
    assert logout_with_csrf.status_code == 200

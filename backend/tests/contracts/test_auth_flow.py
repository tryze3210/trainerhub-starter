from django.contrib.auth import get_user_model
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
    access_token = login_response.json()['access_token']

    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    me_response = client.get('/api/v1/auth/me/')
    assert me_response.status_code == 200
    assert me_response.json()['user']['email'] == 'owner@example.com'

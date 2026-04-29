import pytest


@pytest.fixture()
def user_factory(django_user_model):
    def factory(**kwargs):
        email = kwargs.pop('email', 'factory@example.com')
        password = kwargs.pop('password', 'pass12345')
        return django_user_model.objects.create_user(email=email, password=password, **kwargs)

    return factory
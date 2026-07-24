from .base import *  # noqa: F401,F403

SECRET_KEY = 'trainerhub-test-secret-key-with-safe-length-v167'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
            'SERIALIZE': False,
        },
    }
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'trainerhub-test',
    }
}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CELERY_TASK_ALWAYS_EAGER = True
VK_S3_ENDPOINT_URL = ''
VK_S3_ACCESS_KEY_ID = ''
VK_S3_SECRET_ACCESS_KEY = ''

"""
Test-specific Django settings.

Usage:
    python manage.py test --settings=AgileAllstars.test_settings
    # or via environment variable:
    DJANGO_SETTINGS_MODULE=AgileAllstars.test_settings python manage.py test
"""
from .settings import *  # noqa: F401, F403

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_agile_auth.sqlite3',
    },
    'projects': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_agile_projects.sqlite3',
    },
}

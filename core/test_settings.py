import os


# Minimal env defaults for test runs.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "*")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "True")

# Default local/CI DB creds (match docker-compose/CI defaults).
os.environ.setdefault("POSTGRES_DB", "printdb")
os.environ.setdefault("POSTGRES_USER", "print_user")
os.environ.setdefault("POSTGRES_PASSWORD", "print_pass")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "15432")

from .settings import *  # noqa: F403


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


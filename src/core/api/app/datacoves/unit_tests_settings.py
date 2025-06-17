import os

from datacoves.settings import *  # noqa
from datacoves.settings import BASE_DIR

CELERY_ALWAYS_EAGER = True

SECRET_KEY = "test"

FERNET_KEY = "R2CqeA2xncRDTxlepFZF22oJRnxdVmWfO1-pDXYJAS0="

BILLING_ENABLED = True

BASE_DOMAIN = "datacoveslocal.com"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

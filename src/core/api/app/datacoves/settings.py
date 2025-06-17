import base64
import json
import re
import socket
import sys
from datetime import datetime, timedelta
from os import environ
from pathlib import Path

import sentry_sdk
from celery.schedules import crontab
from corsheaders import defaults
from sentry_sdk.integrations.django import DjangoIntegration

# Utils

BASE_DIR = Path(__file__).resolve().parent.parent  # Usage: BASE_DIR / 'subdir'


def to_bool(s):
    return s.lower() in ("yes", "y", "true", "t", "1")


def env_bool(key, default=False):
    return to_bool(environ[key]) if key in environ else default


# Global, general settings

SECRET_KEY = environ.get("SECRET_KEY")

FERNET_KEY = environ.get("FERNET_KEY")

DEBUG = env_bool("DEBUG")

WSGI_APPLICATION = "datacoves.wsgi.application"
ASGI_APPLICATION = "datacoves.asgi.application"

REDIS_URL = environ.get("REDIS_URI")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

ROOT_URLCONF = "datacoves.urls"

ALLOWED_HOSTS = [
    socket.gethostbyname(socket.gethostname()),  # Prometheus monitoring
    "core-api-svc.core.svc",
    "core-api-svc.core",
    "core-api-svc",
    "api.datacoveslocal.com",
    ".datacoveslocal.com",
] + environ.get("ALLOWED_HOSTS", "").split(",")

CORS_ORIGIN_ALLOW_ALL = False

BASE_DOMAIN = environ.get("BASE_DOMAIN")

CORS_ALLOWED_ORIGIN_REGEXES = (
    [
        rf".*{re.escape(BASE_DOMAIN)}",
    ]
    if BASE_DOMAIN
    else []
)
# New header required by sentry to trace requests
CORS_ALLOW_HEADERS = defaults.default_headers + ("sentry-trace",)

CORS_ALLOW_CREDENTIALS = True

# INSTALLED_APPS reads from the bottom.
# Add new apps at the top of a section, not at the bottom.
INSTALLED_APPS = [
    "daphne",
    # datacoves apps
    "core.apps.CoreConfig",
    "clusters.apps.ClustersConfig",
    "projects.apps.ProjectsConfig",
    "integrations.apps.IntegrationsConfig",
    "invitations.apps.InvitationsConfig",
    "iam.apps.IAMConfig",
    "users.apps.UsersConfig",
    "codegen.apps.CodegenConfig",
    "billing.apps.BillingConfig",
    "notifications.apps.NotificationsConfig",
    "credentials.apps.CredentialsConfig",
    # libraries
    "corsheaders",
    "django_extensions",
    "django_object_actions",
    "social_django",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "django_filters",
    "django_json_widget",
    "django_celery_results",
    "django_celery_beat",
    "django_prometheus",
    "taggit",
    "grappelli",
    "csvexport",
    # health check apps
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    "health_check.contrib.psutil",
    "health_check.contrib.redis",
    # django.contrib
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "oauth2_provider",
    "django.contrib.admindocs",
    "knox",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "clusters.metrics.DatacovesPrometheusMetricMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "core.middleware.AuthErrorHandlerMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "NAME": environ.get("DB_NAME"),
        "USER": environ.get("DB_USER"),
        "PASSWORD": environ.get("DB_PASS"),
        "HOST": environ.get("DB_HOST", "db"),
        "PORT": environ.get("DB_PORT", "5432"),
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_prometheus.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

TESTING = "test" in sys.argv

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_COLLAPSED": True,
    "SHOW_TOOLBAR_CALLBACK": "clusters.debug_toolbar.show_toolbar",
}

if not TESTING:
    INSTALLED_APPS = [
        *INSTALLED_APPS,
        "debug_toolbar",
    ]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]

if TESTING:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "assets"

# What bucket will we use for S3 assets?  Not used by development (yet)
STATIC_S3_BUCKET = environ.get(
    "STATIC_S3_BUCKET", "datacoves-us-east-1-core-api-assets"
)

# For production, we need to have the static URL based on the Cluster database
# model.  To avoid a circular dependency, we'll use a custom storage class.
if not DEBUG:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "datacoves.storage.S3",
        }
    }

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Auth settings

LOGIN_URL = "/iam/login"
LOGIN_ERROR_URL = "/iam/login-error"
LOGIN_REDIRECT_URL = f"https://{BASE_DOMAIN}" if BASE_DOMAIN else None
LOGOUT_REDIRECT = environ.get("LOGOUT_REDIRECT", f"https://{BASE_DOMAIN}/sign-in")
LOGOUT_REDIRECT_URL = "/iam/logout"  # Admin logout url

AUTH_USER_MODEL = "users.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation"
        ".UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "datacoves.csrf_exempt_auth_class.CsrfExemptSessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # This will authorize tokens on all our classes by default.
        # I don't think we want that -- I think we want it to work in
        # very specific spots.  Leaving this here so it is easy to
        # enable if we choose to do so (and so the reasoning why is
        # also known)
        # "knox.auth.TokenAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "1000/hour", "user": "2000/hour"},
}

SIMPLE_JWT = {
    "TOKEN_OBTAIN_SERIALIZER": "iam.serializers.MyTokenObtainPairSerializer",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

KNOX_TOKEN_MODEL = "iam.DatacovesToken"

REST_KNOX = {
    "TOKEN_TTL": None,  # don't expire tokens
    "TOKEN_MODEL": "iam.DatacovesToken",
}

# FIXME: Remove this setting to avoid security vulnerabilities, and configure
# SOCIAL_AUTH_ALLOWED_REDIRECT_HOSTS properly
SOCIAL_AUTH_SANITIZE_REDIRECTS = False

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_TRAILING_SLASH = False  # Remove trailing slash from routes
SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "iam.auth_pipeline.load_user",
    "iam.auth_pipeline.add_to_group_by_role",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

IDENTITY_PROVIDER = environ.get("IDENTITY_PROVIDER")

# OIDC claims need to be prefixed with a namespace
# https://auth0.com/docs/secure/tokens/json-web-tokens/create-namespaced-custom-claims
IDP_SCOPE_NAMESPACE = "https://datacoves.com/"
IDP_SCOPE_CLAIMS = ["openid", "profile", "email"]
IDP_GROUPS_CLAIM = environ.get("IDP_GROUPS_CLAIM")
# User model fields that can't be modified
PROTECTED_USER_FIELDS = ["first_name", "last_name", "iam_groups"]

# Some IDPs don't allow the groups claim, although they send them in the token (Azure AD)
IDP_SEND_GROUPS_CLAIM = env_bool("IDP_SEND_GROUPS_CLAIM")
if IDP_SEND_GROUPS_CLAIM and IDP_GROUPS_CLAIM:
    IDP_SCOPE_CLAIMS.append(IDP_GROUPS_CLAIM)

IDP_OIDC_USER_ID = "email"

if IDENTITY_PROVIDER == "auth0":
    AUTHENTICATION_BACKENDS = ["iam.backends.auth0.Auth0OAuth2"]
    SOCIAL_AUTH_AUTH0_DOMAIN = environ["AUTH0_DOMAIN"]
    SOCIAL_AUTH_AUTH0_KEY = environ["AUTH0_CLIENT_ID"]
    SOCIAL_AUTH_AUTH0_SECRET = environ["AUTH0_CLIENT_SECRET"]
    SOCIAL_AUTH_AUTH0_SCOPE = IDP_SCOPE_CLAIMS
    SOCIAL_AUTH_AUTH0_AUTH_EXTRA_ARGUMENTS = {"prompt": "select_account"}
    IDP_URL = f"https://{SOCIAL_AUTH_AUTH0_DOMAIN}"
    IDP_CLIENT_ID = SOCIAL_AUTH_AUTH0_KEY
    IDP_CLIENT_SECRET = SOCIAL_AUTH_AUTH0_SECRET

elif IDENTITY_PROVIDER == "ping_one":
    AUTHENTICATION_BACKENDS = ["iam.backends.ping.PingOneOpenIdConnect"]
    SOCIAL_AUTH_PING_URL = environ["PING_URL"]
    SOCIAL_AUTH_PING_ONE_KEY = environ["PING_CLIENT_ID"]
    SOCIAL_AUTH_PING_ONE_SECRET = environ["PING_CLIENT_SECRET"]
    SOCIAL_AUTH_PING_ONE_SCOPE = IDP_SCOPE_CLAIMS
    IDP_URL = SOCIAL_AUTH_PING_URL
    IDP_CLIENT_ID = SOCIAL_AUTH_PING_ONE_KEY
    IDP_CLIENT_SECRET = SOCIAL_AUTH_PING_ONE_SECRET

elif IDENTITY_PROVIDER == "ping_federate":
    AUTHENTICATION_BACKENDS = ["iam.backends.ping.PingFederateOpenIdConnect"]
    SOCIAL_AUTH_PING_URL = environ["PING_URL"]
    SOCIAL_AUTH_PING_FEDERATE_KEY = environ["PING_CLIENT_ID"]
    SOCIAL_AUTH_PING_FEDERATE_SECRET = environ["PING_CLIENT_SECRET"]
    SOCIAL_AUTH_PING_FEDERATE_SCOPE = IDP_SCOPE_CLAIMS
    IDP_URL = SOCIAL_AUTH_PING_URL
    IDP_CLIENT_ID = SOCIAL_AUTH_PING_FEDERATE_KEY
    IDP_CLIENT_SECRET = SOCIAL_AUTH_PING_FEDERATE_SECRET

elif IDENTITY_PROVIDER == "azuread-tenant-oauth2":
    IDP_OIDC_USER_ID = "preferred_username"
    AUTHENTICATION_BACKENDS = ["iam.backends.azuread.AzureADTenantOAuth2"]
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = "https://graph.microsoft.com/"
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = environ["AZUREAD_CLIENT_ID"]
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = environ["AZUREAD_CLIENT_SECRET"]
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = environ["AZUREAD_TENANT_ID"]
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SCOPE = IDP_SCOPE_CLAIMS
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_AUTH_EXTRA_ARGUMENTS = {
        "prompt": "select_account"
    }
    IDP_URL = f"https://login.microsoftonline.com/{SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID}/v2.0"
    IDP_CLIENT_ID = SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY
    IDP_CLIENT_SECRET = SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
else:
    AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

# If explicitly enabling user and password authentication in addition to oauth
if IDENTITY_PROVIDER and env_bool("USER_AND_PASS_AUTH"):
    AUTHENTICATION_BACKENDS.append("django.contrib.auth.backends.ModelBackend")

SERVICE_AIRBYTE = "airbyte"
SERVICE_AIRFLOW = "airflow"
SERVICE_LOCAL_DBT_DOCS = "local-dbt-docs"
SERVICE_DBT_DOCS = "dbt-docs"
SERVICE_SUPERSET = "superset"
SERVICE_CODE_SERVER = "code-server"
SERVICE_LOCAL_AIRFLOW = "local-airflow"
SERVICE_DATAHUB = "datahub"

SERVICES = [
    SERVICE_AIRBYTE,
    SERVICE_AIRFLOW,
    SERVICE_CODE_SERVER,
    SERVICE_LOCAL_DBT_DOCS,
    SERVICE_DBT_DOCS,
    SERVICE_SUPERSET,
    SERVICE_DATAHUB,
]

# Billing
INSTANCE_SERVICES = [
    SERVICE_AIRBYTE,
    SERVICE_AIRFLOW,
    SERVICE_SUPERSET,
    SERVICE_DATAHUB,
]

INTERNAL_SERVICE_MINIO = "minio"
INTERNAL_SERVICE_POMERIUM = "pomerium"
INTERNAL_SERVICE_ELASTIC = "elastic"
INTERNAL_SERVICE_NEO4J = "neo4j"
INTERNAL_SERVICE_POSTGRESQL = "postgresql"
INTERNAL_SERVICE_KAFKA = "kafka"
INTERNAL_SERVICE_GRAFANA = "grafana"

INTERNAL_SERVICES = [
    INTERNAL_SERVICE_MINIO,
    INTERNAL_SERVICE_POMERIUM,
    INTERNAL_SERVICE_ELASTIC,
    INTERNAL_SERVICE_NEO4J,
    INTERNAL_SERVICE_POSTGRESQL,
    INTERNAL_SERVICE_KAFKA,
    INTERNAL_SERVICE_GRAFANA,
]

USER_SERVICES = [SERVICE_CODE_SERVER, SERVICE_LOCAL_DBT_DOCS, SERVICE_LOCAL_AIRFLOW]

CLUSTER_SERVICES = [INTERNAL_SERVICE_GRAFANA]

# These are the default resources on workbench
WORKBENCH_RESOURCES = [f"workbench:{service}" for service in SERVICES]

# These are the default resources on dbt-api
# They are created when an Environment is created.
DBT_API_RESOURCES = ["{cluster_domain}:{env_slug}|dbt-api:manifest|write"]

DBT_API_URL = "http://core-dbt-api-svc.core.svc.cluster.local:80"
DBT_API_UPLOAD_MANIFEST_URL = (
    "http://core-dbt-api-svc.core.svc.cluster.local:80/api/internal/manifests"
)

# --------- More granular services resources -----------------

# --- AIRFLOW ----
# if granted read action on 'workbench:airflow', it assumes 'viewer'
# if granted write action on 'workbench:airflow', it assumes 'admin' (all privileges)
SERVICE_AIRFLOW_SECURITY = (
    f"workbench:{SERVICE_AIRFLOW}:security"  # write action -> 'admin' role
)
SERVICE_AIRFLOW_ADMIN = (
    f"workbench:{SERVICE_AIRFLOW}:admin"  # write action -> 'op' role
)
SERVICE_AIRFLOW_SYS_ADMIN = (
    f"workbench:{SERVICE_AIRFLOW}:sysadmin"  # write action -> 'sysadmin' role
)
SERVICE_AIRFLOW_DAGS = (
    f"workbench:{SERVICE_AIRFLOW}:dags"  # write action -> 'user' role
)
WORKBENCH_RESOURCES.append(SERVICE_AIRFLOW_SECURITY)  # resources under 'security' menu
WORKBENCH_RESOURCES.append(SERVICE_AIRFLOW_ADMIN)  # resources under 'admin' menu
WORKBENCH_RESOURCES.append(
    SERVICE_AIRFLOW_SYS_ADMIN
)  # resources under mix 'admin' menu
WORKBENCH_RESOURCES.append(SERVICE_AIRFLOW_DAGS)  # resources under 'browse' menu

# --- SUPERSET ----
# if granted read action on 'workbench:superset', it assumes 'Gamma'
# if granted write action on 'workbench:superset', it assumes 'Admin' (all privileges)
SERVICE_SUPERSET_SECURITY = (
    f"workbench:{SERVICE_SUPERSET}:security"  # write action -> 'Admin' role
)
SERVICE_SUPERSET_DATA_SOURCES = (
    f"workbench:{SERVICE_SUPERSET}:data-sources"  # write action -> 'Alpha' role
)
WORKBENCH_RESOURCES.append(SERVICE_SUPERSET_SECURITY)  # resources under 'security' menu
WORKBENCH_RESOURCES.append(SERVICE_SUPERSET_DATA_SOURCES)  # resources under 'data' menu

# --- DATAHUB ----
# if granted read action on 'workbench:datahub', it assumes 'viewer'
# if granted write action on 'workbench:datahub', it assumes 'admin' (all privileges)
SERVICE_DATAHUB_ADMIN = (
    f"workbench:{SERVICE_DATAHUB}:admin"  # write action -> 'admin' role
)
SERVICE_DATAHUB_DATA = (
    f"workbench:{SERVICE_DATAHUB}:data"  # write action -> 'editor' role
    # read action -> 'viewer' role
)
WORKBENCH_RESOURCES.append(SERVICE_DATAHUB_ADMIN)
WORKBENCH_RESOURCES.append(SERVICE_DATAHUB_DATA)


ADMIN_GROUPS_RESOURCE = "admin:groups"
ADMIN_USERS_RESOURCE = "admin:users"
ADMIN_INVITATIONS_RESOURCE = "admin:invitations"
ADMIN_SECRETS_RESOURCE = "admin:secrets"

SERVICE_GRAFANA_CONFIGURATION = f"services:{INTERNAL_SERVICE_GRAFANA}:configuration"
SERVICE_GRAFANA_DASHBOARDS = f"services:{INTERNAL_SERVICE_GRAFANA}:dashboards"

IAM_RESOURCES = [
    ADMIN_GROUPS_RESOURCE,
    ADMIN_USERS_RESOURCE,
    ADMIN_INVITATIONS_RESOURCE,
]

ACCOUNT_RESOURCES = [
    "admin:environments",
    "admin:projects",
    ADMIN_GROUPS_RESOURCE,
    ADMIN_USERS_RESOURCE,
    ADMIN_INVITATIONS_RESOURCE,
    "admin:connectiontemplates",
    "admin:connectiontypes",
    "admin:servicecredentials",
    "admin:servicesecrets",
    "admin:billing",
    "admin:integrations",
    ADMIN_SECRETS_RESOURCE,
    "admin:templates",
    "admin:profiles",
    f"services:{INTERNAL_SERVICE_GRAFANA}",
    SERVICE_GRAFANA_CONFIGURATION,  # Entire configuration menu
    SERVICE_GRAFANA_DASHBOARDS,  # Dashboards
]

VALID_RESOURCES = WORKBENCH_RESOURCES + ACCOUNT_RESOURCES

ACTION_READ = "read"
ACTION_WRITE = "write"

VALID_ACTIONS = [ACTION_READ, ACTION_WRITE]

DEFAULT_DOCKER_CONFIG = {}
docker_config = environ.get("DEFAULT_DOCKER_CONFIG")
if docker_config:
    docker_config = base64.decodebytes(bytes(docker_config, "ascii"))
    docker_config = json.loads(docker_config)
    DEFAULT_DOCKER_CONFIG = docker_config

# External services

STRIPE_WEBHOOK_SECRET = environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_API_KEY = environ.get("STRIPE_API_KEY")
STRIPE_CUSTOMER_PORTAL = environ.get("STRIPE_CUSTOMER_PORTAL")
STRIPE_RETRY_TIMES = environ.get("STRIPE_RETRY_TIMES", 3)

BILLING_ENABLED = STRIPE_API_KEY is not None


PROMETHEUS_API_URL = "http://prometheus-kube-prometheus-prometheus.prometheus.svc.cluster.local:9090/api/v1"

# Invitations

DEFAULT_FROM_EMAIL = environ.get("DEFAULT_FROM_EMAIL", "no-reply@datacoves.com")
INVITATION_EXPIRY_DAYS = 3
INVITATION_SUCCESS_REDIRECT = LOGIN_URL
INVITATION_ERROR_URL = "/invitations/error"
INVITATION_MAX_ATTEMPTS = 3
SETUP_REQUESTS_RECEIVER = "support@datacoves.com"

# Email configuration

SENDGRID_API_KEY = environ.get("SENDGRID_API_KEY")

if SENDGRID_API_KEY:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.sendgrid.net"
    EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
    EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
elif environ.get("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = environ.get("EMAIL_HOST")
    EMAIL_HOST_USER = environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = environ.get("EMAIL_HOST_PASSWORD")
    EMAIL_PORT = environ.get("EMAIL_PORT", 25)
    EMAIL_USE_TLS = env_bool(key="EMAIL_USE_TLS")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery configuration

CELERY_BROKER_URL = environ.get("CELERY_BROKER_URL")
CELERY_BROKER_HEARTBEAT = None
CELERY_BROKER_CONNECTION_TIMEOUT = 30
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_BACKEND = "django-db"
CELERY_EVENT_QUEUE_EXPIRES = 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_CONCURRENCY = 3
CELERY_TASK_IGNORE_RESULT = False

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "UTC"
CELERY_CREATE_MISSING_QUEUES = True
CELERY_TASK_DEFAULT_EXCHANGE = "default"
CELERY_TASK_DEFAULT_ROUTING_KEY = "default"
# https://stackoverflow.com/questions/32022401/changing-celery-default-queue-not-working-properly-as-expected
CELERY_TASK_DEFAULT_QUEUE = "api-main"
CELERY_TASK_ROUTES = {
    "billing.*": {"queue": "api-long"},
}

CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True

CELERY_ALWAYS_EAGER = False
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERYD_MAX_TASKS_PER_CHILD = 1000
CELERY_EVENT_QUEUE_TTL = 10
CELERY_SEND_EVENTS = True

# Run all celery tasks locally when testing
CELERY_TASK_ALWAYS_EAGER = False
RUN_TASKS_SYNCHRONOUSLY = False

DJANGO_CELERY_BEAT_TZ_AWARE = False

# Verify your crontab syntax with https://crontab.guru. The crontab function
# defaults to "*" for unspecified arguments.
CELERY_BEAT_SCHEDULE = {
    "turn_off_unused_workspaces": {
        "task": "projects.tasks.turn_off_unused_workspaces",
        "schedule": crontab(minute="*/15"),  # Every 15 minute.
    },
    "stop_sharing_codeservers": {
        "task": "projects.tasks.stop_sharing_codeservers",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes.
    },
    "tally_resource_usage": {
        "task": "billing.tasks.tally_resource_usage",
        "schedule": crontab(minute="5", hour="0"),  # At 00:05, every day.
    },
    "inform_billing_events": {
        "task": "billing.tasks.inform_billing_events",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes.
    },
    "celery_heartbeat": {
        "task": "clusters.tasks.celery_heartbeat",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes.
    },
    "clear_tokens": {
        "task": "iam.tasks.clear_tokens",
        "schedule": crontab(minute="10", hour="0"),  # At 00:10, every day.
    },
    "delete_unused_project_keys": {
        "task": "projects.tasks.delete_unused_project_keys",
        "schedule": crontab(minute="20", hour="0"),  # At 00:20, every day.
    },
    "delete_unused_user_keys": {
        "task": "projects.tasks.delete_unused_user_keys",
        "schedule": crontab(minute="23", hour="0"),  # At 00:23, every day.
    },
    "sync_groups": {
        "task": "iam.tasks.remove_missing_user_groups",
        "schedule": crontab(minute="25", hour="0"),  # At 00:25, every day.
    },
    "remove_unused_user_volumes": {
        "task": "projects.tasks.remove_unused_user_volumes",
        "schedule": crontab(minute="30", hour="0"),  # At 00:30, every day.
    },
    "remove_unused_environments": {
        "task": "projects.tasks.remove_unused_environments",
        "schedule": crontab(minute="35", hour="0"),  # At 00:35, every day.
    },
    "delete_cluster_alerts_older": {
        "task": "clusters.tasks.delete_cluster_alerts_older",
        "schedule": crontab(minute="40", hour="0"),  # At 00:40, every day.
    },
    "update_grafana_datasources": {
        "task": "clusters.tasks.update_grafana_datasources",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes.
    },
    "remove_k8s_resources": {
        "task": "clusters.tasks.remove_k8s_resources",
        "schedule": crontab(minute="50", hour="0"),  # At 00:50, every day.
    },
    "deactivate_users": {
        "task": "projects.tasks.deactivate_users",
        "schedule": crontab(minute="55", hour="0"),  # At 00:55, every day.
    },
    "prometheus_metrics": {
        "task": "clusters.tasks.prometheus_metrics",
        "schedule": crontab(minute="*/2"),  # Every 2 minutes.
    },
}

# Tallies

# When TALLY_START env var is not found, tallymarks are not generated
TALLY_START = (
    datetime.fromisoformat(environ["TALLY_START"] + " 00:00+00:00")
    if environ.get("TALLY_START")
    else None
)
TALLY_WINDOW = timedelta(days=31)

TALLY_AIRFLOW_WORKERS_NAME = "airflow_workers_daily_running_time_seconds"
TALLY_AIRBYTE_WORKERS_NAME = "airbyte_workers_daily_running_time_seconds"

# Sentry configuration

SENTRY_DSN = environ.get("SENTRY_DSN")
DISABLE_SENTRY = env_bool("DISABLE_SENTRY")
if SENTRY_DSN and not DISABLE_SENTRY:
    # Sentry
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=BASE_DOMAIN,
        release=environ["RELEASE"],
        integrations=[DjangoIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.001,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        # To set a uniform sample rate
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production,
        profiles_sample_rate=0.01,
        # Alternatively, to control sampling dynamically
        # profiles_sampler=profiles_sampler
    )
    sentry_sdk.set_tag("identity_provider", IDENTITY_PROVIDER)
    sentry_sdk.set_tag("version", environ["VERSION"])

# OIDC server configuration

OAUTH_OIDC_RSA_KEY = environ.get("OAUTH_OIDC_RSA_KEY", "").replace("\\n", "\n")

OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    "OIDC_RSA_PRIVATE_KEY": OAUTH_OIDC_RSA_KEY,
    "PKCE_REQUIRED": False,  # FIXME: This should be True
    "OAUTH2_VALIDATOR_CLASS": "iam.oauth_validators.CustomOAuth2Validator",
    "SCOPES": {
        "openid": "OpenID Connect scope",
        "profile": "",
        "email": "",
        "groups": "Groups user belong to",
    },
}
AUTHENTICATION_BACKENDS.append("oauth2_provider.backends.OAuth2Backend")

# Slack token
SLACK_BOT_TOKEN = environ.get("SLACK_BOT_TOKEN", "")
SLACK_BILLING_CHANNEL = environ.get("SLACK_BILLING_CHANNEL", "bot-billing-events")
SLACK_CLUSTER_CHANNEL = environ.get("SLACK_CLUSTER_CHANNEL", "bot-cluster-events")


# LDAP configuration
LDAP_HOST = environ.get("LDAP_HOST")
LDAP_USERNAME = environ.get("LDAP_USERNAME")
LDAP_PASSWORD = environ.get("LDAP_PASSWORD")
LDAP_FILTER_QUERY = environ.get("LDAP_FILTER_QUERY")
LDAP_BASE = environ.get("LDAP_BASE")

# Logging config
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] - {%(filename)s:%(lineno)d}: %(message)s",
        },
        "simple": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "cli": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "clusters.config_loader": {
            "handlers": ["cli"],
            "level": "INFO",
            "propagate": False,
        },
        "projects.management": {
            "handlers": ["cli"],
            "level": "INFO",
            "propagate": False,
        },
        "projects.git": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Prometheus metrics
# PROMETHEUS_METRIC_NAMESPACE = "datacoves"
PROMETHEUS_EXPORT_MIGRATIONS = False

# CSV export feature
CSV_EXPORT_REFERENCE_DEPTH = 2
CSV_EXPORT_ESCAPECHAR = "\\"

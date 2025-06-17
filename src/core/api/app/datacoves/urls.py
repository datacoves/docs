"""datacoves URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from billing import views as billing_views
from clusters import views as cluster_views
from codegen import views as codegen_views
from credentials import views as credentials_views
from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from iam import views as iam_views
from integrations import views as integrations_views
from invitations import views as invitation_views
from projects import views as projects_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from users import views as users_views

admin.site.site_header = "Datacoves"
admin.site.index_title = "Cluster administration"
admin.site.site_title = "Datacoves Administration"
# Disable user and pass form when using 3rd party auth
if "django.contrib.auth.backends.ModelBackend" in settings.AUTHENTICATION_BACKENDS:
    admin.site.login_template = "admin/combined_login.html"
else:
    admin.site.login_template = "admin/sso_login.html"


urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("grappelli/", include("grappelli.urls")),
    # ------- Login / logout related endpoints -----------------------------
    path(r"healthcheck/", include("health_check.urls")),
    path(r"healthz/", cluster_views.healthcheck),
    # ------- Login / logout related endpoints -----------------------------
    path("", include("social_django.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token_jwt_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_jwr_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_jwt_verify"),
    path("api/datacoves/verify/", iam_views.ValidateDatacovesToken.as_view()),
    path("iam/login", iam_views.login, name="login"),
    path("iam/login-error", iam_views.login_error),
    path("iam/logout", iam_views.logout),
    path("api/iam/accounts", iam_views.UserAccounts.as_view()),
    path("api/iam/user-info", iam_views.UserInfo.as_view()),
    # ------- Profile related endpoints ----------------------------
    path("api/iam/profile", iam_views.ProfileDetail.as_view()),
    path("api/iam/profile/credentials", iam_views.ProfileCredentialList.as_view()),
    path(
        "api/iam/profile/credentials/<int:pk>",
        iam_views.ProfileCredentialDetail.as_view(),
    ),
    path("api/iam/profile/ssh-keys", iam_views.ProfileSSHKeyList.as_view()),
    path("api/iam/profile/ssh-keys/<int:pk>", iam_views.ProfileSSHKeyDetail.as_view()),
    path("api/iam/profile/ssl-keys", iam_views.ProfileSSLKeyList.as_view()),
    path("api/iam/profile/ssl-keys/<int:pk>", iam_views.ProfileSSLKeyDetail.as_view()),
    path(
        "invitations/<str:invite_key>/accept",
        invitation_views.AcceptInvite.as_view(),
        name="accept-invite",
    ),
    path(
        "api/iam/profile/user-environment/<int:pk>/variables",
        iam_views.UserEnvironmentVariablesDetail.as_view(),
    ),
    path("invitations/error", invitation_views.invite_error),
    # ------- Admin User and groups related endpoints ----------------------------
    path("api/admin/<str:account_slug>/groups", iam_views.GroupList.as_view()),
    path(
        "api/admin/<str:account_slug>/groups/<int:pk>",
        iam_views.GroupDetail.as_view(),
    ),
    path("api/admin/<str:account_slug>/users", iam_views.UserList.as_view()),
    path(
        "api/admin/<str:account_slug>/users/<int:pk>",
        iam_views.UserDetail.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/permissions",
        iam_views.AccountPermissionList.as_view(),
    ),
    path("api/admin/<str:account_slug>/settings", iam_views.AccountDetail.as_view()),
    # ------- Admin invitations --------------------------------------------------
    path(
        "api/admin/<str:account_slug>/invitations",
        invitation_views.InvitationList.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/invitations/<int:pk>",
        invitation_views.InvitationDetail.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/invitations/<int:pk>/resend",
        invitation_views.ResendInvitation.as_view(),
    ),
    # ------- Admin Account and project related endpoints ------------------------
    path(
        "api/admin/<str:account_slug>/projects",
        projects_views.ProjectList.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/projects/<int:pk>",
        projects_views.ProjectDetail.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/projects/<int:pk>/keys",
        projects_views.ProjectKeys.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/projects/<int:pk>/keys/<str:token>",
        projects_views.ProjectKeys.as_view(),
    ),
    path(
        "api/admin/adapters/default-values",
        projects_views.AdaptersDefaultValues.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/environments",
        projects_views.EnvironmentList.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/environments/<int:pk>",
        projects_views.EnvironmentDetail.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/environments/<int:pk>/keys",
        projects_views.EnvironmentKeys.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/environments/<int:pk>/keys/<str:token>",
        projects_views.EnvironmentKeys.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/connectiontemplates",
        projects_views.ConnectionTemplateList.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/connectiontemplates/<int:pk>",
        projects_views.ConnectionTemplateDetail.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/integrations",
        integrations_views.IntegrationList.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/templates",
        codegen_views.TemplateList.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/integrations/<int:pk>",
        integrations_views.IntegrationDetail.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/servicecredentials",
        projects_views.ServiceCredentialList.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/servicecredentials/<int:pk>",
        projects_views.ServiceCredentialDetail.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/servicesecrets",
        projects_views.ServiceSecretList.as_view(),
    ),
    # ------- Accounts related endpoints (user belonging to account) ------------------------
    path(
        "api/accounts/<str:account_slug>/connectiontemplates",
        projects_views.ProjectConnectionTemplateList.as_view(),
    ),
    path(
        "api/accounts/<str:account_slug>/connectiontypes",
        projects_views.ConnectionTypeList.as_view(),
    ),
    # ------- Account Setup related endpoints ------------------------
    path(
        "api/setup/test-db-connection",
        projects_views.TestDbConnection.as_view(),
    ),
    path("api/setup/generate-ssh-key", projects_views.GenerateSSHKey.as_view()),
    path("api/setup/generate-ssl-key", projects_views.GenerateSSLKey.as_view()),
    path(
        "api/setup/test-git-connection",
        projects_views.TestGitConnection.as_view(),
    ),
    path(
        "api/billing/subscribe",
        billing_views.SubscribeAccount.as_view(),
    ),
    path(
        "api/accounts/setup",
        projects_views.AccountSetup.as_view(),
    ),
    path(
        "api/webhook",
        projects_views.AdmissionWebHookApiView.as_view(),
    ),
    path("api/setup/notify", users_views.NotifySetupRequest.as_view()),
    path(
        "api/setup/<int:pk>/accept",
        users_views.AcceptSetupRequest.as_view(),
        name="accept-setup",
    ),
    path(
        "api/setup/<int:pk>/reject",
        users_views.RejectSetupRequest.as_view(),
        name="reject-setup",
    ),
    # ------- Workbench related endpoints -----------------------------------------
    path(
        "api/workbench/<str:environment_slug>/status",
        cluster_views.WorkbenchStatus.as_view(),
    ),
    path(
        "api/workbench/<str:environment_slug>/heartbeat",
        cluster_views.WorkbenchHeartbeat.as_view(),
    ),
    path(
        "api/workbench/<str:environment_slug>/code-server/start-local-airflow",
        cluster_views.WorkbenchCodeServerStartLocalAirflow.as_view(),
    ),
    path(
        "api/workbench/<str:environment_slug>/code-server/restart",
        cluster_views.WorkbenchCodeServerRestart.as_view(),
    ),
    path(
        "api/workbench/<str:environment_slug>/code-server/settings",
        cluster_views.WorkbenchCodeServerSettings.as_view(),
    ),
    path(
        "api/alerts",
        cluster_views.AlertView.as_view(),
    ),
    # ------- Credentials/Secrets related endpoints -----------------------------
    path(
        "api/admin/<str:account_slug>/secrets", credentials_views.SecretList.as_view()
    ),
    path(
        "api/admin/<str:account_slug>/secrets/<int:pk>",
        credentials_views.SecretDetail.as_view(),
    ),
    path(
        "api/v1/secrets/<str:slug>",
        credentials_views.PublicSecretList.as_view(),
    ),
    path(
        "api/v1/secret-push/<str:slug>",
        projects_views.push_secrets_variable_to_airflow,
    ),
    path(
        "api/v1/secrets-fetch/<str:slug>",
        projects_views.TeamAirflowSecretFetchView.as_view(),
    ),
    # ------- Profiles related endpoints -----------------------------
    path("api/admin/<str:account_slug>/profiles", projects_views.ProfileList.as_view()),
    path(
        "api/admin/profileimageset/<int:pk>/done/",
        projects_views.ProfileImageSetHook.as_view(),
    ),
    path(
        "api/admin/<str:account_slug>/profiles/<int:pk>",
        projects_views.ProfileDetail.as_view(),
    ),
    # ------- Billing related endpoints -----------------------------------------
    path(
        "api/billing/stripe",
        billing_views.stripe_webhook,
    ),
    # ------- Admin panel --------------------------------------------------
    path("panel/docs/", include("django.contrib.admindocs.urls")),
    path("panel/logout/", iam_views.logout),
    path("panel/", admin.site.urls),
    path("auth/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    # ------- Internal only endpoints -----------------------------------------
    path(
        "api/v1/gitcallback/<str:uid>",
        projects_views.dynamic_repo_credentials,
    ),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns.append(path("", lambda request: redirect("/panel")))
    urlpatterns.append(path("grappelli-docs/", include("grappelli.urls_docs")))

if not settings.TESTING:
    urlpatterns = [
        *urlpatterns,
    ] + debug_toolbar_urls()

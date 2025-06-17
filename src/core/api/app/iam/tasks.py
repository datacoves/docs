from collections import defaultdict

from celery import shared_task
from django.conf import settings
from iam.auth_pipeline import _remove_missing_groups
from users.models import ExtendedGroup, User

from datacoves.celery import app


@shared_task
def clear_tokens():
    from oauth2_provider.models import clear_expired

    clear_expired()


def _get_ldap_credentials():
    return {
        "host": settings.LDAP_HOST,
        "username": settings.LDAP_USERNAME,
        "password": settings.LDAP_PASSWORD,
    }


def get_ldap_group_users(host, username, password, group_name):
    import ldap

    # prevent ssl verification
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

    l = ldap.initialize(host)
    l.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
    l.set_option(ldap.OPT_TIMELIMIT, 0)
    l.set_option(ldap.OPT_DEREF, ldap.DEREF_NEVER)
    l.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
    l.set_option(ldap.OPT_X_TLS_DEMAND, True)
    l.set_option(ldap.OPT_DEBUG_LEVEL, 255)

    # login
    l.bind(username, password)
    l.result()

    filter_query = (settings.LDAP_FILTER_QUERY or "{group}").format(group=group_name)
    query = l.search_ext(
        settings.LDAP_BASE,
        ldap.SCOPE_SUBTREE,
        filter_query,
        ["*"],
        attrsonly=0,
        timeout=-1,
        sizelimit=0,
    )
    response = l.result(query, all=1, timeout=-1)
    user_mails = []
    for user in response[1]:
        user_response = user[1]
        user_mail = user_response.get("mail")
        if isinstance(user_mail, list) and len(user_mail):
            user_mail = user_mail[0]
            if isinstance(user_mail, bytes):
                user_mail = user_mail.decode()
            user_mails.append(user_mail)
    return user_mails


def _get_groups_name():
    group_names = []
    identity_groups_query = ExtendedGroup.objects.values_list(
        "identity_groups", flat=True
    )
    for identity_group in identity_groups_query:
        if isinstance(identity_group, list):
            group_names.extend(identity_group)

    # avoid duplicate groups in the list
    group_names = list(set(group_names))
    return group_names


@app.task
def remove_missing_user_groups():
    credentials = _get_ldap_credentials()
    host = credentials.get("host")
    username = credentials.get("username")
    password = credentials.get("password")

    if not host or not username or not password:
        return

    group_names = _get_groups_name()

    # association is a dict like { <user1>: [ group1, group2 ], <user2>: [ group3 ] }
    associations = defaultdict(list)
    for group_name in group_names:
        response = get_ldap_group_users(host, username, password, group_name)
        for user in response:
            associations[user.upper()].append(group_name)
    for user in User.objects.exclude(deactivated_at__isnull=False).exclude(
        is_superuser=True
    ):
        user_group_names = associations.get(user.email.upper(), [])
        _remove_missing_groups(user, user_group_names)

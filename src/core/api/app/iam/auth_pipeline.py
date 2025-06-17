import logging

from django.conf import settings
from social_core.exceptions import AuthMissingParameter
from users.models import ExtendedGroup, User

logger = logging.getLogger(__name__)


def load_user(backend, details, response, *args, **kwargs):
    """
    Gets user from DB by email, if doesn't exist creates it.
    """

    user_email = details.get("email")

    logger.info(f"load_user: {user_email}")

    if user_email is None:
        logger.error("load_user: missing parameter 'email'")
        raise AuthMissingParameter(backend, "email")

    user_name = details.get("fullname")

    logger.info(f"load_user: {user_name}")

    if user_name is None:
        logger.error("load_user: missing parameter 'fullname'")
        raise AuthMissingParameter(backend, "fullname")

    user, _ = User.objects.update_or_create(
        email__iexact=user_email,
        defaults={"name": user_name, "email": user_email, "deactivated_at": None},
    )

    logger.info(f"load_user: {user_email} is user ID {user.id}")

    return {"user": user}


def add_to_group_by_role(strategy, backend, details, response, user, *args, **kwargs):
    """
    Adds user to group based on identity provider's role/group name
    """

    group_claim = settings.IDP_GROUPS_CLAIM

    logger.info(details)
    logger.info(response)

    if group_claim:
        group_names = details.get("iam_groups")
        if group_names is None:
            logger.info("add_to_group_by_role: no iam_groups")
            group_names = []
        elif type(group_names) is str:
            logger.info(f"add_to_group_by_role: group is {group_names}")
            group_names = [group_names]
        else:
            logger.info(f"add_to_group_by_role: group is {', '.join(group_names)}")

        # groups are removed only if a group claim was configured
        _remove_missing_groups(user, group_names)

        if group_names:
            for g_name in group_names:
                extended_groups = ExtendedGroup.objects.filter(
                    identity_groups__contains=g_name
                ).select_related("group")
                for extended_group in extended_groups:
                    logger.info(f"add_to_group_by_role: matched eg {extended_group.id}")

                    group = extended_group.group

                    if group:
                        logger.info(f"add_to_group_by_role: adding group {group.id}")

                        if not user.groups.filter(id=group.id).exists():
                            user.groups.add(group)

                    else:
                        logger.info(
                            "add_to_group_by_role: extended group wasn't mapped to a group"
                        )


def _remove_missing_groups(user, group_names):
    """
    Removes groups that are in the DB but not in the token
    """
    # don't remove groups that are not tied to an IDP group (custom added groups)
    qs = user.groups.exclude(extended_group__identity_groups=[])

    for group_name in group_names:
        qs = qs.exclude(extended_group__identity_groups__contains=group_name)

    for group in qs:
        logger.info(f"Removing group {group} from user {user}")
        user.groups.remove(group)

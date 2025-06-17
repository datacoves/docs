from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from projects.models.environment import Environment
from users.models import Account

from .metrics import MetricsCacheKeyEnum


@receiver(post_save, sender=Account)
@receiver(post_delete, sender=Account)
def clear_account_cache(sender, **kwargs):
    cache.delete(MetricsCacheKeyEnum.ACCOUNT_INFO.value)
    cache.delete(MetricsCacheKeyEnum.ENVIRONMENT_INFO.value)
    cache.delete(MetricsCacheKeyEnum.HELM_CHART_INFO.value)


@receiver(post_save, sender=Environment)
@receiver(post_delete, sender=Environment)
def clear_environment_cache(sender, **kwargs):
    cache.delete(MetricsCacheKeyEnum.ENVIRONMENT_INFO.value)
    cache.delete(MetricsCacheKeyEnum.HELM_CHART_INFO.value)

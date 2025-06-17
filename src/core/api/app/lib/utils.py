"""
Utilities that don't quite fit somewhere else yet. This is useful when you come
up with a function that is generic and you don't know where to put it yet.
Don't let this file grow too big. Move things out of here once it is clearer
where to put them.
"""

# TODO: This file shoudn't depend on django, redis, celery, etc. When running
# from cli.py or a regular ipython shell it forces us to install all those
# packages which we don't need. Make a separate module for django utils.

import logging
import time
from contextlib import ContextDecorator, contextmanager
from datetime import date, datetime, timedelta, timezone
from functools import reduce, wraps

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


def m2m_changed_subjects_and_objects(kwargs):
    if not kwargs["reverse"]:
        subjects = [kwargs["instance"]]
        objects = kwargs["pk_set"]
    else:
        subjects = kwargs["model"].objects.filter(pk__in=kwargs["pk_set"])
        objects = {kwargs["instance"].pk}
    return subjects, objects


def date_to_datetime(d):
    assert isinstance(d, date)
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def now():
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)


def yesterday():
    return date_to_datetime((now() - timedelta(days=1)).date())


def day_interval_until_now(day):
    from django.utils import timezone as django_timezone

    t_a, t_b = day_interval(day)
    now = django_timezone.now().timestamp()
    return min(t_a, now), min(t_b, now)


def day_interval(day):
    day = date_to_datetime(day)
    t_a = day.timestamp()
    t_b = (day + timedelta(days=1)).timestamp()
    return t_a, t_b


@contextmanager
def task_lock(lock_id):
    from django.core.cache import cache
    from redis.exceptions import LockError

    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    lock = cache.lock(lock_id, timeout=LOCK_EXPIRE)
    status = lock.acquire(blocking=False)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            try:
                lock.release()
            except LockError:
                pass


def get_pending_tasks(task_name):
    """Get pending tasks for a given task_name"""
    from datacoves.celery import app

    matched_tasks = []
    inspect = app.control.inspect()
    reserved = inspect.reserved()
    if reserved:
        tasks = reduce(lambda x, y: x + y, reserved.values())
        for task in tasks:
            if task.get("type") == task_name:
                matched_tasks.append(task)
    return matched_tasks


def cancel_pending_task(task_id: str):
    from datacoves.celery import app

    app.control.revoke(task_id)


def same_dicts_in_lists(list1, list2):
    """Check if lists contain the same dictionaries in any order."""
    return len(list1) == len(list2) and all(x in list2 for x in list1)


# Define a custom function to serialize datetime objects
def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def force_ipv4(func):
    import requests

    def wrapper(*args, **kwargs):
        has_ipv6 = requests.packages.urllib3.util.connection.HAS_IPV6
        try:
            requests.packages.urllib3.util.connection.HAS_IPV6 = False
            return func(*args, **kwargs)
        finally:
            requests.packages.urllib3.util.connection.HAS_IPV6 = has_ipv6

    return wrapper


class Timer(ContextDecorator):
    def __init__(self, name="Process"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        elapsed_time = self.end_time - self.start_time
        logger.info(f"{self.name} took {elapsed_time:.4f} seconds")


def cache_result(timeout=3600, key_prefix=None):
    from django.core.cache import cache

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_elements = [key_prefix or func.__name__]
            if args:
                key_elements.extend(map(str, args))
            if kwargs:
                key_elements.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_elements)

            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator

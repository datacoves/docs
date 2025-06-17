import datetime

from django.contrib.admin import BooleanFieldListFilter, DateFieldListFilter
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseModelAdmin:
    change_list_template = "admin/change_list_filter_sidebar.html"


class DefaultNoBooleanFilter(BooleanFieldListFilter):
    def choices(self, changelist):
        field_choices = dict(self.field.flatchoices)
        # Switching All by No and vice-versa
        for lookup, title in (
            (None, _("No")),
            ("1", field_choices.get(True, _("Yes"))),
            ("0", field_choices.get(False, _("All"))),
        ):
            yield {
                "selected": self.lookup_val == lookup and not self.lookup_val2,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg: lookup}, [self.lookup_kwarg2]
                ),
                "display": title,
            }
        if self.field.null:
            yield {
                "selected": self.lookup_val2 == "True",
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg2: "True"}, [self.lookup_kwarg]
                ),
                "display": field_choices.get(None, _("Unknown")),
            }

    def queryset(self, request, queryset):
        # Switching All by No and vice-versa
        if (
            self.lookup_kwarg in self.used_parameters
            and isinstance(self.used_parameters[self.lookup_kwarg], list)
            and len(self.used_parameters[self.lookup_kwarg])
            and not int(self.used_parameters[self.lookup_kwarg][0])
        ):
            # This handles the 'all' case
            del self.used_parameters[self.lookup_kwarg]
        elif (
            not self.used_parameters
            or self.used_parameters.get(self.lookup_kwarg) is None
        ):
            self.used_parameters[self.lookup_kwarg] = [0]

        return super().queryset(request, queryset)


class DateFieldListFilterExtended(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = "%s__" % field_path
        self.date_params = {
            k: v[-1] for k, v in params.items() if k.startswith(self.field_generic)
        }

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        if today.month == 1:
            last_month = today.replace(year=today.year - 1, month=12, day=1)
        else:
            last_month = today.replace(month=today.month - 1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)

        self.lookup_kwarg_since = "%s__gte" % field_path
        self.lookup_kwarg_until = "%s__lt" % field_path
        self.links = (
            (_("Any date"), {}),
            (
                _("Today"),
                {
                    self.lookup_kwarg_since: today,
                    self.lookup_kwarg_until: tomorrow,
                },
            ),
            (
                _("Past 7 days"),
                {
                    self.lookup_kwarg_since: today - datetime.timedelta(days=7),
                    self.lookup_kwarg_until: tomorrow,
                },
            ),
            (
                _("This month"),
                {
                    self.lookup_kwarg_since: today.replace(day=1),
                    self.lookup_kwarg_until: next_month,
                },
            ),
            (
                _("Last month"),
                {
                    self.lookup_kwarg_since: last_month,
                    self.lookup_kwarg_until: today.replace(day=1),
                },
            ),
            (
                _("Past 30 days"),
                {
                    self.lookup_kwarg_since: today - datetime.timedelta(days=30),
                    self.lookup_kwarg_until: tomorrow,
                },
            ),
            (
                _("Past 180 days"),
                {
                    self.lookup_kwarg_since: today - datetime.timedelta(days=180),
                    self.lookup_kwarg_until: tomorrow,
                },
            ),
            (
                _("This year"),
                {
                    self.lookup_kwarg_since: today.replace(month=1, day=1),
                    self.lookup_kwarg_until: next_year,
                },
            ),
            (
                _("Last year"),
                {
                    self.lookup_kwarg_since: today.replace(
                        year=today.year - 1, month=1, day=1
                    ),
                    self.lookup_kwarg_until: today.replace(month=1, day=1),
                },
            ),
        )
        if field.null:
            self.lookup_kwarg_isnull = "%s__isnull" % field_path
            self.links += (
                (_("No date"), {self.field_generic + "isnull": True}),
                (_("Has date"), {self.field_generic + "isnull": False}),
            )
        super(DateFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path
        )


class DeactivatedDateFilter(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = "%s__" % field_path
        self.date_params = {
            k: v[-1] for k, v in params.items() if k.startswith(self.field_generic)
        }

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)

        self.lookup_kwarg_since = "%s__gte" % field_path
        self.lookup_kwarg_until = "%s__lt" % field_path
        self.lookup_kwarg_isnull = "%s__isnull" % field_path
        self.links = (
            # this used to be the `Any date` value
            (_("Active"), {}),
            (_("Inactive"), {self.lookup_kwarg_isnull: False}),
            # this used to be the `No date` value
            (_("All"), {self.lookup_kwarg_isnull: True}),
            (
                _("Today"),
                {
                    self.lookup_kwarg_since: today,
                    self.lookup_kwarg_until: tomorrow,
                },
            ),
            (
                _("Past 7 days"),
                {
                    self.lookup_kwarg_since: today - datetime.timedelta(days=7),
                    self.lookup_kwarg_until: tomorrow,
                },
            ),
            (
                _("This month"),
                {
                    self.lookup_kwarg_since: today.replace(day=1),
                    self.lookup_kwarg_until: next_month,
                },
            ),
            (
                _("This year"),
                {
                    self.lookup_kwarg_since: today.replace(month=1, day=1),
                    self.lookup_kwarg_until: next_year,
                },
            ),
        )
        super(DateFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path
        )

    def queryset(self, request, queryset):
        if (
            self.used_parameters.get(self.lookup_kwarg_isnull)
            and self.used_parameters.get(self.lookup_kwarg_isnull)[0]
        ):
            del self.used_parameters[self.lookup_kwarg_isnull]
        elif (
            not self.used_parameters
            or self.used_parameters.get(self.lookup_kwarg_isnull) is None
        ):
            self.used_parameters[self.lookup_kwarg_isnull] = [True]
        return super().queryset(request, queryset)

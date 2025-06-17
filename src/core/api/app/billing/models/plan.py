from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.db import models

from .product import Product


def get_default_workers_execution_limit():
    return {"airflow": 36000, "airbyte": 36000}


class Plan(AuditModelMixin, DatacovesModel):
    """
    A Plan is describes a set of products and services provided to Accounts,
    and how they will pay for them (how often, at what prices, etc.).

    E.g.: Starter Monthly, Starter yearly, Growth Monthly, Growth Yearly.
    A Plan is a stripe Subscription modulo the Account.

    =========
    Constants
    =========

    ----
    Type
    ----

     - KIND_STARTER
     - KIND_GROWTH
     - KIND_CUSTOM
     - KINDS - a tuple of tuple pairs for select box.

    ------
    Period
    ------

     - PERIOD_MONTHLY
     - PERIOD_YEARLY
     - PERIODS - a tuple of tuple pairs for select box


    =======
    Methods
    =======

     - **save** is overriden to make defaults for slug and name (see table below)
     - **variant_items(variant)** - Unpacks the Stripe items from the
       'variants' list as a list of dictionaries for a given variant name.
     - **prices(variant)** - Return a dictionary of price ID's mapping to price
       for a given variant name.
     - **checkout_items(variant)** - Returns a list of price entries for
       Stripe checkout based on what services we can bill for the given variant
     - **products(variant)** - Returns a queryset of :model:`billing.Product`
       objects associated with a given variant.
     - **seat_price(variant)** - Returns a dictionary mapping Stripe price ID
       to price amount for associated charge-by-seat products, or None if there
       are no such products as part of this plan.
     - **service_price(service, variant)** - Returns a dictionary mapping
       Stripe price ID to price amount for associated flat-fee service products, or
       None if there are no such products as part of this plan.
     - **tally_price(tally, variant)** - Returns a dictionary mapping Stripe
       price ID to price amount for associated tally-based (i.e utilization
       based) products, or None if there are no such products as part of this
       plan.
     - **tally_service_price(tally, variant)** - Returns a dictionary mapping
       Stripe price ID to price amount for associated tally-based
       (i.e utilization based) products that are associated with a service,
       or None if there are no such products as part of this plan.
     - **get_metered_price_by_service(service_name, variant)** -
       Metered products have 'service_name' set to the service name
     - **informs_usage(variant)** - If contains metered prices, returns true
    """

    slug = models.SlugField(
        unique=True,
        help_text="starter-monthly, starter-yearly, etc.  If left blank, "
        "this will be automatically set based on kind and period.",
    )

    name = models.CharField(
        max_length=50,
        help_text="Human readable name.  If left blank, this will be set based on kind and period.",
    )

    KIND_STARTER = "starter"
    KIND_GROWTH = "growth"
    KIND_CUSTOM = "custom"
    KINDS = (
        (KIND_STARTER, "Starter"),
        (KIND_GROWTH, "Growth"),
        (KIND_CUSTOM, "Custom"),
    )
    kind = models.CharField(
        max_length=20, choices=KINDS, default=KIND_STARTER, help_text="The type of plan"
    )

    PERIOD_MONTHLY = "monthly"
    PERIOD_YEARLY = "yearly"
    PERIODS = (
        (PERIOD_MONTHLY, "Monthly"),
        (PERIOD_YEARLY, "Yearly"),
    )
    billing_period = models.CharField(
        max_length=20,
        choices=PERIODS,
        default=PERIOD_MONTHLY,
        help_text="The frequency of billing",
    )

    trial_period_days = models.PositiveIntegerField(
        default=0, help_text="Zero means no trial period."
    )

    # variants : {"standard": [{"price": price}, ...]}
    # There could be multiple prices with different amounts for the same plan so
    # that the commercial team has flexibility to negotiate prices.
    variants = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="JSON list of Stripe subscription items to allow multiple prices for a given plan.",
    )

    environment_quotas = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="The default environment quota -- this can be overriden "
        "per environment.  The format is a Kubernetes resource quota: "
        "https://kubernetes.io/docs/concepts/policy/resource-quotas/",
    )

    workers_execution_limit = models.JSONField(
        default=get_default_workers_execution_limit,
        null=True,
        help_text="max execution seconds allowed per period at plan level",
    )
    developer_licenses = models.PositiveIntegerField(
        default=0,
        help_text="Max number of developer licenses (users with access to at least "
        "one code-server pod), zero means infinite.",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{self.kind}-{self.billing_period}"

        if not self.name:
            kind_nice = self.kind.replace("-", " ").capitalize()
            billing_period_nice = self.billing_period.capitalize()
            self.name = f"{kind_nice} - {billing_period_nice}"

        super().save(*args, **kwargs)

    def variant_items(self, variant: str) -> list:
        """Unpacks the Stripe items from the 'variants' list as a list of
        dictionaries for a given variant name.
        """

        return [
            list(v.values())[0]["items"] for v in self.variants if variant in v.keys()
        ][0]

    def prices(self, variant: str) -> dict:
        """Return a dictionary of price ID's mapping to price for a given
        variant name.
        """

        return {
            item["price"]["id"]: item["price"] for item in self.variant_items(variant)
        }

    @property
    def is_starter(self) -> bool:
        """Returns boolean, True if plan is a starter plan"""

        return self.kind == self.KIND_STARTER

    @property
    def is_monthly(self) -> bool:
        """Returns boolean, True if plan is a monthly plan"""

        return self.billing_period == self.PERIOD_MONTHLY

    def checkout_items(self, variant: str) -> list:
        """Returns a list of price entries of type "licensed" for a Stripe checkout.
        It double checks that the products are not associated to services nor tallies,
        so it effectively returns just developer seat prices"""

        noservice_products = Product.objects.filter(
            service_name="", tally_name=""
        ).values_list("id", flat=True)

        # Note that quantity is always 1 since during checkout only one developer has been
        # created, the rest is created later and events should be informed accordingly
        return [
            {"price": item["price"]["id"], "quantity": 1}
            for item in self.variant_items(variant)
            if item["price"].get("recurring", {}).get("usage_type", "") == "licensed"
            and item["price"]["product"] in noservice_products
        ]

    def products(self, variant: str):
        """Returns a queryset of :model:`billing.Product` objects associated
        with a given variant."""

        product_ids = [
            price["product"] for price in self.prices(variant=variant).values()
        ]
        return Product.objects.filter(id__in=product_ids)

    def seat_price(self, variant: str):
        """Returns a dictionary mapping Stripe price ID to price amount
        for associated charge-by-seat products, or None if there are no
        such products as part of this plan.
        """

        seat_products = Product.objects.filter(charges_per_seat=True).values_list(
            "id", flat=True
        )

        for price in self.prices(variant=variant).values():
            if price["product"] in seat_products:
                return price

        return None

    def service_price(self, service: str, variant: str):
        """Returns a dictionary mapping Stripe price ID to price amount
        for associated flat-fee service products, or None if there are no
        such products as part of this plan.
        """

        service_products = (
            Product.objects.filter(service_name=service)
            .filter(tally_name="")
            .values_list("id", flat=True)
        )

        for price in self.prices(variant=variant).values():
            if price["product"] in service_products:
                return price

        return None

    def tally_price(self, tally: str, variant: str):
        """Returns a dictionary mapping Stripe price ID to price amount
        for associated tally-based (i.e utilization based) products,
        or None if there are no such products as part of this plan.
        """

        tally_products = Product.objects.filter(tally_name=tally).values_list(
            "id", flat=True
        )
        for price in self.prices(variant=variant).values():
            if price["product"] in tally_products:
                return price
        return None

    def tally_service_price(self, tally: str, variant: str):
        """Returns a dictionary mapping Stripe price ID to price amount
        for associated tally-based (i.e utilization based) products that
        are associated with a service, or None if there are no such products
        as part of this plan.
        """

        tally_product = Product.objects.filter(tally_name=tally).first()
        service_name = None

        if tally_product:
            service_name = tally_product.service_name

        service_product = (
            Product.objects.filter(service_name=service_name)
            .exclude(tally_name=tally_product.name)
            .values_list("id", flat=True)
        )

        for price in self.prices(variant=variant).values():
            if price["product"] in service_product:
                return price

        return None

    def get_metered_price_by_service(self, service_name: str, variant: str):
        """Metered products have 'service_name' set to the service name"""
        metered_product = (
            Product.objects.filter(service_name=service_name)
            .exclude(tally_name="")
            .first()
        )
        assert (
            metered_product is not None
        ), f"No metered billing found in Products with service name {service_name}"
        prices = [
            price
            for price in self.prices(variant=variant).values()
            if price["product"] == metered_product.id
        ]
        if prices:
            return prices[0]
        return None

    def informs_usage(self, variant: str) -> bool:
        """If contains metered prices, returns true"""
        for item in self.prices(variant).values():
            if item.get("recurring", {}).get("usage_type", "") == "metered":
                return True
        return False

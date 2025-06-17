from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from django.conf import settings
from django.db import models

from .tally import Tally


class Product(AuditModelMixin, DatacovesModel):
    """Products are our local representation of Stripe products

    This is the mapping between our database's understanding of products
    and Stripe's, essentially a mapping to stripe product IDs.  We
    use their product ID as the primary key here (id).

    This is managed by a combination of products set up in stripe, and
    cli.py's download_pricing_model method.  This, in turn, is driven by
    the 'pricing.yaml' file which is in the cluster config.

    Note that 'save' is overriden on this Model in order to implement the
    inference of service_name and tally_name.
    """

    # id, name, description and stripe_data mirror stripe.
    id = models.CharField(
        max_length=40,
        primary_key=True,
        help_text="This should match the corresponding Stripe product ID; it will start with prod_",
    )
    name = models.CharField(
        max_length=100, help_text="Human readable, descriptive name of product"
    )
    description = models.TextField(
        null=True, blank=True, help_text="Additional description if needed."
    )
    stripe_data = models.JSONField(
        default=dict,
        help_text="JSON dictionary which is a representation of the Stripe object (i.e. what Stripe uses in its API)",
    )
    charges_per_seat = models.BooleanField(
        default=False,
        help_text="If charges per user with access to at least one code-server pod",
    )
    service_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Used to associate services that need to be charged by "
        "instance.  This may be set for you if left blank and we can infer "
        "it from the 'name'.",
    )
    tally_name = models.SlugField(
        null=True,
        blank=True,
        help_text="The name of a tally that keeps track of the usage for "
        "this product.  See :model:`billing.Tally`  This may be set for you "
        "if left blank and 'name' contains 'airbyte' or 'airflow' in "
        "addition to the word 'compute'",
    )

    def tallies(self):
        """Tallies associated with this Product.  Only works if tally_name is
        set."""

        return Tally.objects.filter(name=self.tally_name)

    def __str__(self):
        return f"{self.id} ({self.name})"

    def save(self, *args, **kwargs):
        """Sets 'service_name' and 'tally_name' if they are not already set
        and we can infer the values.

        'service_name' will be set if 'server' or 'compute' are in the
        'name' field.  It will be set to whatever service matches first
        in the settings.SERVICES field.

        'tally_name' will be set if 'compute' is in the 'name' field and
        if 'airflow' or 'airbyte' is in the field.  'airbyte' will win if,
        for some reason, both words are present.
        """

        # Looking for a service using the product name
        lower_name = self.name.lower()

        if not self.service_name and (
            "server" in lower_name or "compute" in lower_name
        ):
            for service in settings.SERVICES:
                if service.lower() in lower_name:
                    self.service_name = service
                    break

        # Connecting product with actual tallies
        if not self.tally_name:
            if "airflow" in lower_name and "compute" in lower_name:
                self.tally_name = settings.TALLY_AIRFLOW_WORKERS_NAME
            if "airbyte" in lower_name and "compute" in lower_name:
                self.tally_name = settings.TALLY_AIRBYTE_WORKERS_NAME

        super().save(*args, **kwargs)

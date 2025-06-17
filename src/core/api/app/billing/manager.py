import logging
from datetime import datetime, timedelta

import stripe
from billing.models import Account, Plan
from django.conf import settings
from django.utils import timezone

from .models import Credit, Event, Tally, TallyMark

# For now, we configure stripe globally here, once and for all. If another
# module needs to use stripe (which most shouldn't), they should also import
# this module so that these settings are applied.
stripe.api_key = settings.STRIPE_API_KEY
stripe.max_network_retries = settings.STRIPE_RETRY_TIMES


DAYS_UNTIL_DUE = 5  # days until invoices due


def create_checkout_session(account, plan_slug, variant, domain):
    """
    Creates a checkout session for the given account, plan, and variant
    This method can be used only when we want to charge for developer seats
    """
    customer_email = account.owned_by.email
    if not account.customer_id:
        # create and link stripe customer to datacoves account.
        customer = stripe.Customer.create(email=customer_email, name=account.slug)
        account.customer_id = customer.id
        account.save()
    else:
        customer = stripe.Customer.retrieve(id=account.customer_id)

    plan = Plan.objects.get(slug=plan_slug)
    success_url = (
        f"https://{domain}/admin/billing/checkout?session_id=" + "{CHECKOUT_SESSION_ID}"
    )
    cancel_url = f"https://{domain}/admin/billing/cancel"
    session = stripe.checkout.Session.create(
        line_items=plan.checkout_items(variant),
        mode="subscription",
        automatic_tax={"enabled": True},
        customer=customer,
        customer_update={"address": "auto", "name": "auto"},
        subscription_data={"metadata": {"plan": plan.slug}},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    account.plan = plan
    account.variant = variant
    account.settings["last_checkout_session"] = session
    account.save()


def handle_checkout_session_completed(event):
    session = event.data.object
    account = Account.objects.get(customer_id=session.customer)
    account.customer_id = session["customer"]
    now = timezone.now()
    if account.trial_ends_at and account.trial_ends_at > now:
        account.trial_ends_at = now
    account.save()


def handle_customer_subscription_created(event):
    return handle_customer_subscription_updated(event)


# TODO: https://stripe.com/docs/billing/subscriptions/webhooks#state-changes
def handle_customer_subscription_updated(event):
    subscription = event.data.object
    account = Account.objects.get(customer_id=subscription.customer)
    account.update_from_subscription(subscription)


def handle_customer_subscription_deleted(event):
    subscription = event.data.object
    account = Account.objects.get(customer_id=subscription.customer)
    # account.plan = None
    account.cancelled_subscription = account.subscription
    account.subscription = {}
    account.subscription_updated_at = timezone.now()
    account.save()


def _get_si_for_tally(plan: Plan, variant: str, tally_name: str, subscription: dict):
    """
    Returns subscription item for tally
    """

    price = plan.tally_price(tally_name, variant)
    assert price, f"Price not found for tally {tally_name}"

    service_price = plan.tally_service_price(tally_name, variant)
    assert (
        service_price
    ), f"Price found for tally {tally_name} but no associated service found in subscription"

    items = [si for si in subscription["items"] if si["price"]["id"] == price["id"]]

    assert (
        len(items) == 1
    ), f"No, or more than one subscription item associated to tally {tally_name}"
    return items[0]


def report_usage_to_stripe(account_slug: str):
    """
    Processes all pending tally marks for account_slug
    """

    if not settings.BILLING_ENABLED:
        return
    account = Account.objects.get(slug=account_slug)
    plan = account.plan
    subscribed_at, current_period_start = get_subscription_dates(account)
    for tally in Tally.objects.filter(account=account):
        tally_marks = tally.marks.filter(status=TallyMark.STATUS_PENDING)
        if plan.kind == Plan.KIND_CUSTOM or not plan.informs_usage(account.variant):
            tally_marks.update(status=Event.STATUS_IGNORED, processed_at=timezone.now())
            continue
        try:
            si = _get_si_for_tally(
                plan, account.variant, tally.name, account.subscription
            )
        except Exception as ex:
            error_msg = f"Exception found when attempting to report usage: {str(ex)}"
            logging.error(error_msg)
            raise Exception(error_msg)

        for tally_mark in tally_marks:
            process_tally_mark(tally_mark, subscribed_at, current_period_start, si)


def get_subscription_dates(account):
    """
    Parses subscription and current period dates from
    account.subscription
    Current period should always be up-to-date from
    Stripe webhooks.
    """
    subscribed_at = datetime.fromtimestamp(
        account.subscription["start_date"], timezone.get_default_timezone()
    )
    current_period_start = datetime.fromtimestamp(
        account.subscription["current_period_start"], timezone.get_default_timezone()
    )
    current_period_end = datetime.fromtimestamp(
        account.subscription["current_period_end"], timezone.get_default_timezone()
    )
    # Make sure current period start is correct.
    # If Datacoves is not in sync with Stripe notify of the error.
    utcnow = datetime.now(timezone.get_default_timezone())
    assert_message = (
        f"Cannot report usage for {account.name}"
        f" because database shows current period end: {current_period_end}"
        f" is prior to now: {utcnow}"
    )
    # if plan is 'custom', meaning 'free', this check does not apply:
    if account.plan.kind != Plan.KIND_CUSTOM:
        assert utcnow < current_period_end, assert_message
    return subscribed_at, current_period_start


def process_tally_mark(
    tally_mark: TallyMark,
    subscribed_at: datetime,
    current_period_start: datetime,
    subscription_item: dict,
):
    tally_mark, send_to_stripe_amount = validate_tally_mark(
        tally_mark, subscribed_at, current_period_start
    )
    if tally_mark.status == TallyMark.STATUS_PENDING:
        process_pending_tally_mark(tally_mark, send_to_stripe_amount, subscription_item)


def validate_tally_mark(
    tally_mark: TallyMark, subscribed_at: datetime, current_period_start: datetime
):
    """
    Ignore events prior to the subscription.
    Update tally mark time to current period if mark
    is from last period (Stripe won't accept it)
    """
    send_to_stripe_amount = int(tally_mark.amount / 60)
    if tally_mark.time < subscribed_at:
        # If tally mark was generated before subscription actually started
        tally_mark.status = Event.STATUS_IGNORED
        tally_mark.processed_at = timezone.now()
        tally_mark.save()
    elif tally_mark.time < current_period_start:
        # Usage from yesterday cannot be reported if a new period has started today.
        # Report past usage with timestamp after current period started. Also update tally mark.
        # Also, avoid hitting duplicate index error.
        new_time = current_period_start  # No time earlier than this will be accepted by stripe.
        tally_mark.time = new_time
        exists = (
            TallyMark.objects.filter(tally=tally_mark.tally, time=new_time).count() > 0
        )
        while exists:
            new_time += timedelta(seconds=1)
            tally_mark.time = new_time
            exists = (
                TallyMark.objects.filter(tally=tally_mark.tally, time=new_time).count()
                > 0
            )

    return tally_mark, send_to_stripe_amount


def process_pending_tally_mark(
    tally_mark: TallyMark, send_to_stripe_amount: int, subscription_item: dict
):
    try:
        if send_to_stripe_amount > 0:
            # Don't send usage = 0 to Stripe. Process mark nevertheless.
            stripe.SubscriptionItem.create_usage_record(
                subscription_item["id"],
                quantity=send_to_stripe_amount,
                timestamp=tally_mark.time,
                action="set",
                idempotency_key=str(tally_mark.id),
            )
        tally_mark.status = Event.STATUS_PROCESSED
    except Exception as ex:
        tally_mark.status = Event.STATUS_FAILED
        tally_mark.error_details = str(ex)
        logging.error(tally_mark.error_details)
    finally:
        tally_mark.processed_at = timezone.now()
        tally_mark.save()


def inform_billing_events():
    if not settings.BILLING_ENABLED:
        return

    for event in (
        Event.objects.filter(status=Event.STATUS_PENDING)
        .exclude(approval_status=Event.APPROVAL_PENDING)
        .order_by("id")
    ):
        event.status = Event.STATUS_PROCESSED
        if event.account.is_subscribed and event.account.plan:
            try:
                if event.account.plan.kind == event.account.plan.KIND_STARTER:
                    update_starter_subscription(
                        event.account, event.created_at, len(event.users)
                    )
                elif event.account.plan.kind == event.account.plan.KIND_GROWTH:
                    update_growth_subscription(
                        event.account,
                        event.created_at,
                        len(event.users),
                        event.service_counts,
                    )
                else:
                    # Special plans that are not processed
                    event.status = Event.STATUS_IGNORED
            except Exception as ex:
                event.status = Event.STATUS_FAILED
                event.error_details = str(ex)
        else:
            event.status = Event.STATUS_FAILED
            event.error_details = (
                f"Missing subscription and/or plan in account {event.account}"
            )

        event.processed_at = timezone.now()
        event.save()

        if event.status == Event.STATUS_FAILED:
            logging.error(event.error_details)


def _get_subscription_item_by_price(subscription, price):
    for si in subscription["items"]:
        if si["price"]["id"] == price["id"]:
            return si
    return None


def _get_seats_si(account, quantity):
    """Generates a line item for seats changes"""
    seat_price = account.plan.seat_price(account.variant)

    si = _get_subscription_item_by_price(account.subscription, seat_price)

    new_si = {"quantity": quantity, "price": seat_price["id"]}
    if si:
        new_si["id"] = si["id"]
        if quantity == 0:
            new_si["deleted"] = True
    else:
        if quantity == 0:
            return None
    return new_si


def _get_prorration_date(account: Account, event_date: datetime):
    current = event_date.replace(hour=0, minute=0)
    period_start = datetime.fromtimestamp(
        account.subscription["current_period_start"], timezone.get_default_timezone()
    ).replace(tzinfo=timezone.get_default_timezone())
    return max(current, period_start)


def _get_subscription_params(account, event_date):
    params = {
        "proration_behavior": "create_prorations",
        "collection_method": "charge_automatically",
        "proration_date": _get_prorration_date(account, event_date),
    }
    if not account.plan.is_monthly:
        params["proration_behavior"] = "always_invoice"
        params["collection_method"] = "send_invoice"
        params["days_until_due"] = DAYS_UNTIL_DUE
    return params


def update_starter_subscription(account: Account, event_date: datetime, users: int):
    params = _get_subscription_params(account, event_date)
    stripe.Subscription.modify(
        account.subscription_id, items=[_get_seats_si(account, users)], **params
    )


def _get_service_si(account, service, quantity):
    service_price = account.plan.service_price(service, account.variant)
    assert (
        service_price is not None
    ), f"Missing service price for plan {account.plan} and service {service}. \
         Please verify that Product and Price exist on Stripe and have been synced to database."
    si = _get_subscription_item_by_price(account.subscription, service_price)
    new_si = {"quantity": quantity, "price": service_price["id"]}
    if si:
        new_si["id"] = si["id"]
        if quantity == 0:
            new_si["deleted"] = True
    else:
        if quantity == 0:
            return None
    return new_si


def _get_metered_si(account, service_name):
    service_name = service_name.lower()
    metered_price = account.plan.get_metered_price_by_service(
        service_name, account.variant
    )
    if metered_price:
        new_si = {"price": metered_price["id"]}
        si = _get_subscription_item_by_price(account.subscription, metered_price)
        if si:
            new_si["id"] = si["id"]
        return new_si
    return None


def update_growth_subscription(
    account: Account, event_date: datetime, users: int, services
):
    """
    Process a growth plan subscription update.
    If there is a credit, it is subtracted from the number of users and services
    """
    params = _get_subscription_params(account, event_date)
    credit = Credit.objects.get_credit(account)

    if credit:
        users -= credit.developer_seats
        services[settings.SERVICE_AIRBYTE] -= credit.airbyte_instances
        services[settings.SERVICE_AIRFLOW] -= credit.airflow_instances
        services[settings.SERVICE_SUPERSET] -= credit.superset_instances
        services[settings.SERVICE_DATAHUB] -= credit.datahub_instances

    seats_si = _get_seats_si(account, users)

    airbyte_si, airbyte_usage_si = _get_airservice_sis(
        account=account, services=services, service_name=settings.SERVICE_AIRBYTE
    )
    airflow_si, airflow_usage_si = _get_airservice_sis(
        account=account, services=services, service_name=settings.SERVICE_AIRFLOW
    )
    superset_si = _get_service_si(
        account, settings.SERVICE_SUPERSET, services[settings.SERVICE_SUPERSET]
    )
    datahub_si = _get_service_si(
        account, settings.SERVICE_DATAHUB, services[settings.SERVICE_DATAHUB]
    )
    items = [
        seats_si,
        airbyte_si,
        airbyte_usage_si,
        airflow_si,
        airflow_usage_si,
        superset_si,
        datahub_si,
    ]

    subscription = stripe.Subscription.modify(
        account.subscription_id,
        items=[item for item in items if item is not None],
        **params,
    )
    account.update_from_subscription(subscription)


def _get_airservice_sis(account: Account, services: dict, service_name: str) -> tuple:
    airservice_si = _get_service_si(account, service_name, services[service_name])
    if airservice_si:
        airservice_usage_si = _get_metered_si(account, service_name)
    else:
        airservice_usage_si = None
    return airservice_si, airservice_usage_si


def cancel_subscription(account):
    if account.is_subscribed:
        stripe.Subscription.delete(account.subscription_id)

from collections import defaultdict
from pathlib import Path

import stripe

from lib.config_files import load_file, write_yaml

DEFAULT_PLAN_VARIANT = "standard"


def set_api_key(cluster_domain):
    path = Path("config") / cluster_domain / "secrets" / "core-api.env"
    stripe.api_key = load_file(path)["STRIPE_API_KEY"]


def download_pricing_model(cluster_domain):
    """
    Downloads pricing model from Stripe
    """
    set_api_key(cluster_domain)
    path = Path("config") / cluster_domain / "pricing.yaml"
    current_model = load_file(path)
    model = pricing_model()
    merge_current_into_new(
        model["products"],
        current_model.get("products", {}),
        {"tally_name": "", "service_name": ""},
    )
    merge_current_into_new(
        model["plans"],
        current_model.get("plans", {}),
        {"environment_quotas": {}, "trial_period_days": 0},
    )
    write_yaml(path, model)


def merge_current_into_new(news, currents, fields):
    for k, new in news.items():
        current = currents.get(k, {})
        for f, default in fields.items():
            new[f] = current.get(f, default)


def pricing_model(cluster_domain=None):
    if cluster_domain:
        set_api_key(cluster_domain)
    products = get_actives(stripe.Product)
    prices = get_actives(stripe.Price)

    prices_by_product = defaultdict(list)
    for price in prices.values():
        if price.product in products:
            prices_by_product[price.product].append(price)

    plans = defaultdict(dict)
    prices_by_plan = defaultdict(list)
    for p in products.values():
        plan_meta = p.metadata.get("plans", p.metadata.get("plan", ""))
        for plan_slug in plan_meta.split(","):
            if not plan_slug:
                continue
            plan = plans[plan_slug]
            kind, billing_period = plan_slug.rsplit("-", 1)
            plan["kind"] = kind
            plan["billing_period"] = billing_period
            plan["prices"] = prices_by_plan[plan_slug]

            for price in prices_by_product[p.id]:
                price_data = price.to_dict_recursive()
                price_data.pop("object")
                assert price_data.pop("active")

                plan["prices"].append(price_data)

    seat_products = []

    for product_id, product in products.items():
        charges_per_seat = product.unit_label == "seat"
        if charges_per_seat:
            seat_products.append(product_id)
        products[product_id] = {
            "id": product_id,
            "name": product.name,
            "description": product.description or "",
            "stripe_data": product.to_dict_recursive(),
            "charges_per_seat": charges_per_seat,
        }

    for plan in plans.values():
        plan["variants"] = plan_prices_to_variants(
            plan["prices"], seat_products, DEFAULT_PLAN_VARIANT
        )
        del plan["prices"]

    return {
        "products": products,
        "plans": dict(plans),
    }


def get_actives(resource_class):
    it = resource_class.list().auto_paging_iter()
    return {p.id: p for p in it if p.active}


def plan_prices_to_variants(prices, seat_products, default_variant):
    """
    Returns a list of 'variants'
    [
        {
            'standard': {
                'default': True,
                'items': []
            }
        }
    ]
    """
    data = []
    # organize prices by nickname: standard, pro (different, customized amounts)
    prices_dict = defaultdict(list)
    for price in prices:
        variant = price.get("nickname") or default_variant
        prices_dict[variant].append(price)

    for variant in prices_dict:
        seat_items = []
        other_items = []
        for price in prices_dict[variant]:
            item = {"price": price}
            if price["product"] in seat_products:
                seat_items.append(item)
            else:
                other_items.append(item)
        # Seat product prices go first as stripe's checkout page features the first item
        items = seat_items + other_items
        data.append({variant: {"items": items, "default": variant == default_variant}})
    return data

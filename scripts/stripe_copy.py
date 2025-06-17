"""
This script was copied from https://gist.github.com/mikegogulski/83ce5f6ac0633ca6cac913d0dab4b9eb
"""

### The best way to start is to use the "Delete all test data" button at https://dashboard.stripe.com/test/developers

import stripe

from scripts.stripe_utils import set_api_key

TEST_DOMAIN = "datacoveslocal.com"

SKIP_FIELDS = [
    "amount_decimal",
    "unit_amount_decimal",
    "type",
    "object",
    "created",
    "livemode",
    "updated",
]
IGNORE_PRODUCTS = [
    "prod_JNXXXyourproductID",
]


def clear_stripe_things(thing: tuple) -> None:
    """
    Clear out test products/prices
    """
    print("Clearing", thing[0])
    for p in getattr(stripe, thing[0]).list():
        print("Clearing", p.get("id"), "-", p.get("name"))
        if p.get("product") in IGNORE_PRODUCTS:
            print("Ignoring")
            continue
        if not p.get("active"):
            print("Inactive, skipping")
            continue
        if p.get("livemode"):
            print("LIVE MODE THING! Skipping")
            continue
        try:
            getattr(stripe, thing[0]).modify(p.get("id"), active=False)
        except Exception as e:
            print("Exception modifying for", p)
            print(e)
            pass
        try:
            p.delete()
        except Exception as e:
            print("Exception deleting for", p.get("id"))
            print(e)
            continue


def upload_products(products) -> None:
    """
    Copy production products to test, preserving IDs
    """
    print("Uploading products")
    up = list()
    for p in products[1].get("data"):
        print("Queueing", p.get("id"), "-", p.get("name"))
        if p.get("product") in IGNORE_PRODUCTS:
            print("Ignoring")
            continue
        up.append({k: v for k, v in p.items() if k not in SKIP_FIELDS})
    for p in up:
        try:
            del p["default_price"]
            print("Uploading", p.get("id"), "-", p.get("name"))
            print(up)
            stripe.Product.create(**p)
        except Exception as e:
            print("EXCEPTION creating", p)
            print("EXCEPTION:", e)
            continue


def upload_prices(products, prices) -> None:
    """
    Upload prices to Stripe, preserving product ID correspondences
    """
    skips = SKIP_FIELDS + ["id", "unit_amount_decimal", "flat_amount_decimal"]
    for p in products[1]:
        print("Uploading for", p.get("id"), "-", p.get("name"))
        if not p.get("active"):
            print("Inactive product, skipping")
            continue

        for prod_price in prices[1]:
            if prod_price.get("product") == p.get("id"):
                # remove the "flat_amount_decimal" and "unit_amount_decimal" keys from the tiers
                for tier in prod_price.get("tiers", []):
                    del tier["flat_amount_decimal"]
                    del tier["unit_amount_decimal"]
                    tier["up_to"] = (
                        "inf" if tier.get("up_to") is None else tier.get("up_to")
                    )
                print("prod_price", prod_price)
                test_price = {k: v for k, v in prod_price.items() if k not in skips}
                print("test_price", test_price)
                try:
                    stripe.Price.create(**test_price)
                except Exception as e:
                    print("EXCEPTION creating price", p)
                    print("EXCEPTION:", e)
                    continue


def copy_to_test(cluster_domain):
    """
    Copies products and prices from a cluster stripe account into
    datacoveslocal.com associated stripe test mode account
    """
    set_api_key(cluster_domain)
    prodproducts = ("Product", stripe.Product.list(active=True, limit=100))
    prodprices = (
        "Price",
        stripe.Price.list(active=True, limit=100, expand=["data.tiers"]),
    )

    set_api_key(TEST_DOMAIN)
    clear_stripe_things(prodprices)
    clear_stripe_things(prodproducts)
    upload_products(prodproducts)
    upload_prices(prodproducts, prodprices)

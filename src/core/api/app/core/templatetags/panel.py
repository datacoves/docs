from clusters.models import Cluster
from django import template
from django.urls import reverse
from grappelli.dashboard.utils import filter_models

register = template.Library()


@register.simple_tag(takes_context=True)
def shortcuts(context):
    request = context["request"]

    amap = {"view": "changelist"}
    nmap = {"view": "{app} / {mp}"}
    admin_links = []
    for model, views in filter_models(request, ["*"], []):
        for view, active in views.items():
            if active and view in amap:
                admin_links.append(
                    {
                        "name": nmap[view].format(
                            mp=model._meta.verbose_name_plural.title(),
                            ms=model._meta.verbose_name.title(),
                            app=model._meta.app_label.replace("_", " / ").title(),
                        ),
                        "url": reverse(
                            f"admin:{model._meta.app_label}_{model.__name__.lower()}_{amap[view]}"
                        ),
                    }
                )
    admin_links.sort(key=lambda o: o["name"])

    return admin_links


@register.simple_tag
def cluster_domain():
    cluster = Cluster.objects.current().first()
    return cluster.domain if cluster else ""


@register.simple_tag
def cluster_admin_color():
    cluster = Cluster.objects.current().first()
    return cluster.settings.get("admin_panel_color") if cluster else "black"

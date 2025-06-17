import re
from functools import cached_property

import sentry_sdk
from core.fields import EncryptedJSONField
from core.mixins.models import AuditModelMixin
from core.models import DatacovesModel
from dateutil import parser
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils import timezone
from notifications.models import AccountNotification

import lib.kubernetes.client as k8s_client


def default_features_enabled():
    return {
        "user_profile_delete_account": False,
        "user_profile_change_name": False,
        "user_profile_change_credentials": False,
        "user_profile_change_ssh_keys": False,
        "user_profile_change_ssl_keys": False,
        "accounts_signup": False,
        "admin_account": False,
        "admin_groups": False,
        "admin_create_groups": False,
        "admin_invitations": False,
        "admin_users": False,
        "admin_projects": False,
        "admin_environments": False,
        "admin_connections": False,
        "admin_service_credentials": False,
        "admin_billing": False,
        "admin_integrations": False,
        "admin_secrets": False,
        "admin_profiles": False,
        "admin_code_server_environment_variables": False,
        "admin_env_code_server_mem_and_cpu_resources": False,
        "admin_env_airflow_mem_and_cpu_resources": False,
        "stop_codeserver_on_inactivity": False,
        "shareable_codeserver": False,
        "codeserver_exposures": False,
        "codeserver_restart": False,
        "block_workers": False,
        "observability_stack": False,
        "select_minio_logs": False,
        "show_get_started_banner": True,
        "local_airflow": False,
        "env_grafana_dashboards_enabled": False,
        "node_local_dns_enabled": False,
    }


def default_docker_config():
    return settings.DEFAULT_DOCKER_CONFIG


def default_limits():
    return {
        "max_cluster_active_accounts": 20,
        # "max_cluster_active_environments": 50,
        "max_cluster_active_trial_accounts": 10,
        # "max_cluster_active_users": 100,
    }


def default_release():
    from projects.models import Release

    latests = Release.objects.get_latests().values_list("id", flat=True)
    return latests[0] if latests else None


def default_alert_system_settings():
    return {"muted_notifications": []}


def default_cluster_settings():
    return {"admin_panel_color": "green", "code_server_inactivity_threshold": 30}


__all__ = ["Cluster", "ClusterAlert"]


class ClusterManager(models.Manager):
    def current(self):
        qs = self.get_queryset()
        return qs.filter(domain=settings.BASE_DOMAIN)


class Cluster(AuditModelMixin, DatacovesModel):
    """A cluster is a set of environments that are all running on a single
    infrastructure provider (EKS, GKE, AKS, or local/Kind).

    The cluster associates the base domain name with the environments,
    controls features, certain global settings, and keeps track of which
    release is being used by the cluster as a whole.

    **Constants**

    --------------
    Provider Types
    --------------

     - EKS_PROVIDER
     - GKE_PROVIDER
     - AKS_PROVIDER
     - KIND_PROVIDER

    ------------------
    Provider Selection
    ------------------

     - PROVIDERS

    Tuple of tuples, with each element tuple having the first element
    being the provider type constant, and the second element being the
    human readable text.

    ------------------
    Logs Backend Types
    ------------------

     - LOGS_BACKEND_S3
     - LOGS_BACKEND_EFS
     - LOGS_BACKEND_AFS
     - LOGS_BACKEND_NFS

    --------------------------
    Airbyte Logs Backend Types
    --------------------------

     - AIRBYTE_LOGS_BACKEND

    Tuple of tuples, with each element tuple having the first element
    be the log backend type and the second element being the human readable
    text.

    --------------------------
    Airflow Logs Backend Types
    --------------------------

     - AIRFLOW_LOGS_BACKEND

    Tuple of tuples, with each element tuple having the first element
    be the log backend type and the second element being the human readable
    text.

    =======
    Methods
    =======

     - **save** is overriden to provide certain default capabilities
     - **has_dynamic_db_provisioning()** - Does this cluster use dynamic
       S3 provisioning?
     - **has_dynamic_network_filesystem_provisioning()** -
       Does this cluster use dynamic EFS provisioning?
     - **has_dynamic_blob_storage_provisioning()** -
       Does this cluster use dynamic S3 provisioning?
     - **is_feature_enabled(feature_code)** - Is the given feature enabled?
     - **has_dynamic_provisioning()** - Are both dynamic DB and dynamic S3
       provisioning turned on?
     - **get_image(repo, release)** - Returns the image name and tag for a
       given repo.  If the cluster uses a different docker registry, it is
       prepended to the image name.
     - **get_service_image(service, repo, tax_prefix, release)** -
       Returns the image name and tag for a given repo and service.
       If the cluster uses a different docker registry, it is
       prepended to the image name.
    """

    EKS_PROVIDER = "eks"
    GKE_PROVIDER = "gke"
    AKS_PROVIDER = "aks"
    KIND_PROVIDER = "kind"

    PROVIDERS = (
        (
            EKS_PROVIDER,
            "EKS (Amazon)",
        ),
        (
            GKE_PROVIDER,
            "GKE (Google)",
        ),
        (
            AKS_PROVIDER,
            "AKS (Azure)",
        ),
        (
            KIND_PROVIDER,
            "Kind (local)",
        ),
    )

    LOGS_BACKEND_S3 = "s3"
    LOGS_BACKEND_EFS = "efs"
    LOGS_BACKEND_AFS = "afs"
    LOGS_BACKEND_NFS = "nfs"
    AIRBYTE_LOGS_BACKEND = (
        (
            LOGS_BACKEND_S3,
            "S3",
        ),
    )
    AIRFLOW_LOGS_BACKEND = (
        (
            LOGS_BACKEND_S3,
            "S3",
        ),
        (
            LOGS_BACKEND_EFS,
            "EFS",
        ),
        (
            LOGS_BACKEND_AFS,
            "AFS",
        ),
        (
            LOGS_BACKEND_NFS,
            "NFS",
        ),
    )

    domain = models.CharField(
        max_length=253,
        unique=True,
        help_text="Base domain name for the cluster, without a leading .",
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDERS,
        default=KIND_PROVIDER,
        help_text="Service Provider for Cluster",
    )
    kubernetes_version = models.CharField(
        max_length=40, help_text="Kubernetes version used by cluster"
    )
    cert_manager_issuer = models.CharField(
        max_length=253,
        null=True,
        blank=True,
        help_text="Sets the cert-manager.io/cluster-issuer annotation on "
        "the cluster ingress - "
        "https://cert-manager.io/docs/configuration/issuers/",
    )
    external_dns_url = models.CharField(
        max_length=253,
        null=True,
        blank=True,
        help_text="Sets the external-dns.alpha.kubernetes.io/target "
        "annotation on the cluster ingress.  This requires provider "
        "support, and allows the creation of automatic DNS records.",
    )
    # This is necessary when on private networks to allow traffic
    internal_dns_url = models.CharField(
        max_length=253,
        null=True,
        blank=True,
        help_text="This is a domain name which is resolved to get the "
        "internal_dns_ip address.  It does not make sense to set both "
        "this and internal_dns_ip.  See that field for more details.",
    )
    internal_dns_ip = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="Used to configure an Egress Rule to use a specific "
        "IP address.  This is used on private networks mostly in order to"
        "access the IP address of a DNS server.  You can "
        "set the Internal DNS URL instead if you want this to be dynamic.",
    )
    internal_db_cluster_ip_range = models.CharField(
        max_length=18,
        null=True,
        blank=True,
        help_text="This is a CIDR-style IP address with netmask (i.e. "
        "192.168.1.0/24).  It is for using a block of IP addresses for "
        "Egress, similar to internal_dns_ip; it probably does not make "
        "sense to use this and the other two internal address fields above.",
    )
    internal_ip = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="The cluster's internal IP address.  If this field is "
        "blank, external_ip should be blank as well, and both IP addresses "
        "will be fetched via Kubernetes' get_ingress_controller_ips call.  "
        "Leaving this blank, but filling in external_ip, will probably cause "
        "the operator to fail.",
    )
    external_ip = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        help_text="The cluster's external IP address.  May be, and often is, " "blank.",
    )
    api_server_ips = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A JSON dictionary with two keys in it; 'ips' and 'ports'.  "
        "'ips' is a list of internal DNS IPs as strings, and 'ports' is the "
        "corresponding list of port numbers as integers.",
    )
    extra_images = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="Currently unused.  This comes from Releases instead.",
    )
    dont_use_uwsgi = models.BooleanField(
        default=False, help_text="Set true for development environments."
    )
    features_enabled = models.JSONField(
        default=default_features_enabled,
        blank=True,
        null=True,
        help_text="Dictionary of feature flags.  There are too many to "
        "document here; see the default_features_enabled method in "
        "api/app/clusters/models/cluster.py",
    )
    limits = models.JSONField(
        default=default_limits,
        blank=True,
        null=True,
        help_text="JSON Dictionary specifying the default cluster usage "
        "limits.  It can have the following keys which map to integer "
        "limits: max_cluster_active_accounts, "
        "max_cluster_active_environments, max_cluster_active_trial_accounts, "
        "max_cluster_active_users ... not all of these are implemented yet.",
    )

    release_channel = models.CharField(
        max_length=20,
        default="edge",
        help_text="Release channel to follow - Not used yet",
    )

    # Release of core services
    release = models.ForeignKey(
        "projects.Release",
        on_delete=models.PROTECT,
        related_name="clusters",
        default=default_release,
        help_text="Which release is being used for core services.",
    )

    # Docker
    docker_registry = models.CharField(
        max_length=253,
        blank=True,
        help_text="Registry to pull images from.  Can be blank for dockerhub.",
    )
    docker_config_secret_name = models.CharField(
        max_length=253,
        default="docker-config-datacovesprivate",
        null=True,
        blank=True,
        help_text="The Kubernetes secret to use with the Docker registry",
    )
    # An empty docker_config means core-api is not responsible for creating the
    # secret, another system creates the secret named docker_config_secret_name.
    docker_config = EncryptedJSONField(
        default=default_docker_config,
        blank=True,
        null=True,
        help_text="If blank, then core-api is not responsible for creating "
        "the Docker config secret; another system creates the secret, "
        "which should be named docker_config_secret_name ... otherwise, "
        "this is a dictionary with an 'auths' key which, in turn, is a "
        "dictionary mapping registry host names to dictionaries of "
        "credential information: username, password, email, and auth",
    )

    grafana_settings = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary of Grafana settings, such as OIDC secrets",
    )
    alert_system_settings = models.JSONField(
        default=default_alert_system_settings,
        blank=True,
        null=True,
        help_text='Alert system settings, such as muted notifs ({"muted_notifications":'
        ' [{"namespace": "cloudwatch", "pod": "~worker-.*", "name": "=ContainerCpuUsage",'
        ' "channel": "slack"}]}).',
    )
    # Config to dynamically create postgres dbs
    postgres_db_provisioner = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="A dictionary with PostgreSQL server information.  It "
        "can have the following keys: host, pass, user, port (int), db ... "
        "If provided, we will automatically create PostgreSQL databases on "
        "the provided server (user/pass should belong to an admin user "
        "which can CREATE DATABASE).  Leave empty to use a database in the "
        "cluster.",
    )

    # Config to dynamically create S3 buckets
    s3_provisioner = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Configuration to dynamically create S3 buckets.  This "
        "should be a dictionary with 'aws_access_key_id', "
        "'aws_secret_access_key' and 'region'.  This enables us to "
        "automatically make S3 buckets as necessary.  If not set, "
        "features that need S3 buckets (such as airflow logs to S3) will "
        "need manual configuration.",
    )

    # Config to dynamically create EFS filesystems
    efs_provisioner = EncryptedJSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Dynamic EFS provisioning is not yet supported; this can "
        "be a dictionary with a 'global' field to fake autoprovisioning; "
        "the global field should contain the fake-provisioned EFS information.",
    )

    airbyte_config = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Default AirByte configuration.  This can be overridden "
        "per-environment.  It is a dictionary, typically with 'db' and "
        "'logs' keys mapping to dictionaries with configuration for both.",
    )

    airflow_config = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Default AirFlow configuration.  This can be overridden "
        "per-environment.  It is a dictionary, usually empty at this level.",
    )

    superset_config = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Default Superset configuration.  This can be overridden "
        "per-environment.  It is a dictionary, usually empty at this level.",
    )

    code_server_config = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Default Code Server configuration.  This can be overridden "
        "per-environment.  It is a dictionary which typically has a "
        "'resources' dictionary of Kubernetes resource allocations, "
        "an 'overprovisioning' dictionary which has settings for hot spares, "
        "and finally a key 'max_code_server_pods_per_node'.  This is not an "
        "exhaustive list.",
    )

    datahub_config = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Default DataHub configuration.  This can be overriden "
        "per-environment.  It is a dictionary, usually empty at this level.",
    )

    celery_heartbeat_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time Celery reported in; not normally edited by users",
    )

    # Cluster general settings
    settings = models.JSONField(
        default=default_cluster_settings,
        null=True,
        blank=True,
        help_text="Configures 'admin_panel_color' (CSS color code) and "
        "'code_server_inactivity_threshold' (minutes)",
    )

    # Config to store service accounts
    service_account = EncryptedJSONField(default=dict, blank=True, null=True)

    objects = ClusterManager()

    def __str__(self):
        return self.domain

    def save(self, *args, **kwargs):
        """This overrides save in order to handle defaulting of internal_ip
        and external_ip, along with api_server_ips.  It also copies
        all_features (default + overriden features) over to features_enabled
        """

        if not self.internal_ip or not self.external_ip:
            kc = self.kubectl
            self.internal_ip, self.external_ip = kc.get_ingress_controller_ips()

        if not self.api_server_ips:
            self.api_server_ips = self.kubectl.get_cluster_apiserver_ips()

        self.features_enabled = self.all_features

        return super().save(*args, **kwargs)

    @property
    def is_local(self) -> bool:
        """Is this a local installation (i.e. uses Kind as a provider)"""
        return self.provider == self.KIND_PROVIDER

    @property
    def upgrade_in_progress(self) -> bool:
        """Are upgrades currently running on the system?"""
        upgrade = self.upgrades.order_by("-id").first()
        return upgrade and upgrade.status == upgrade.STATUS_RUNNING

    @property
    def defines_resource_requests(self) -> bool:
        """Does this cluster have resource requests?"""
        return True  # not self.is_local

    @property
    def all_features(self) -> dict:
        """Default features + overrided features"""
        features = default_features_enabled()
        features.update(self.features_enabled)

        features["accounts_signup"] = (
            features["accounts_signup"]
            and settings.BILLING_ENABLED
            and (self.is_local or self.has_dynamic_provisioning())
        )
        return features

    @property
    def all_limits(self) -> dict:
        """Default limits + overrided limits"""
        limits = default_limits()
        limits.update(self.limits)
        return limits

    def has_dynamic_db_provisioning(self) -> bool:
        """Does this cluster use dynamic DB provisioning?"""
        return bool(self.postgres_db_provisioner)

    def has_dynamic_blob_storage_provisioning(self) -> bool:
        """Does this cluster use dynamic S3 provisioning?"""
        return bool(self.s3_provisioner)

    def has_dynamic_network_filesystem_provisioning(self) -> bool:
        """Does this cluster use dynamic EFS provisioning?"""
        return bool(self.efs_provisioner)

    def is_feature_enabled(self, code: str) -> bool:
        """Is the given feature enabled?"""
        return self.all_features.get(code, False)

    def has_dynamic_provisioning(self) -> bool:
        """Are both dynamic DB and dynamic S3 provisioning turned on?"""
        return (
            self.has_dynamic_db_provisioning()
            and self.has_dynamic_blob_storage_provisioning()
        )

    def get_image(self, repo: str, release=None):
        """
        Returns the image name and tag for a given repo.
        If the cluster uses a different docker registry, it is prepended to the image name.
        """
        rel = release or self.release
        image, tag = rel.get_image(repo)
        if self.docker_registry:
            image = f"{self.docker_registry}/{image}"
        return image, tag

    def get_service_image(self, service: str, repo: str, tag_prefix=None, release=None):
        """
        Returns the image name and tag for a given repo and service.
        If the cluster uses a different docker registry, it is prepended to the image name.
        """
        rel = release or self.release
        image, tag = rel.get_service_image(service, repo, tag_prefix=tag_prefix)
        if self.docker_registry:
            image = f"{self.docker_registry}/{image}"
        return image, tag

    @cached_property
    def kubectl(self):
        """Accessor for the k8s_client Kubectl object"""
        return k8s_client.Kubectl()


class ClusterAlert(DatacovesModel):
    """Not sure what this is -- coming back to it

    =========
    Constants
    =========

     - STATUS_FIRING - Alert is active
     - STATUS_RESOLVED - Alert is resolved
     - STATUS_CHOICES - tuple of tuple pairs for select box
    """

    STATUS_FIRING = "firing"
    STATUS_RESOLVED = "resolved"
    STATUS_CHOICES = [
        (STATUS_FIRING, "Firing"),
        (STATUS_RESOLVED, "Resolved"),
    ]

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    started_at = models.DateTimeField()
    name = models.CharField(max_length=100)
    namespace = models.CharField(max_length=63, null=True, blank=True)
    cluster = models.ForeignKey("clusters.Cluster", on_delete=models.CASCADE)
    environment = models.ForeignKey(
        "projects.Environment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="If this is null, then it is a system alert.",
    )
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=10, null=True, blank=True
    )
    resolved = models.BooleanField(default=False)
    data = models.JSONField()

    def __str__(self):
        return self.summary

    @admin.display(boolean=True)
    def is_system_alert(self):
        return self.environment is None

    @property
    def summary(self):
        """Fetches the 'summary' key from the 'annotations' key of the
        data field"""
        return self.data.get("annotations", {}).get("summary")

    def generate_metadata(self):
        """Method to generate slack metadata."""
        started_at = parser.parse(self.data.get("startsAt"))
        ended_at = parser.parse(self.data.get("endsAt"))
        value = self.data.get("annotations", {}).get("value")
        if ended_at < started_at:
            is_current = True
            failing_time = timezone.now() - started_at
        else:
            is_current = False
            failing_time = ended_at - started_at
        metadata = {
            "alert_type": self.data.get("labels", {}).get("alertname"),
            "cluster": self.cluster.domain,
            "namespace": self.namespace,
            "environment": self.environment.slug if self.environment else None,
            "account": (
                self.environment.project.account.slug if self.environment else None
            ),
            "pod": self.data.get("labels", {}).get("pod"),
            "node": self.data.get("labels", {}).get("node"),
            "failing_time": f"{failing_time.total_seconds()} seconds",
            "value": value,
            "started_at": started_at,
            "severity": self.data.get("labels", {}).get("severity"),
        }
        if not is_current:
            metadata["ended_at"] = ended_at
        return metadata

    def generate_extra_fields(self):
        fields = [
            "persistentvolumeclaim",
            "phase",
            "device",
            "fstype",
            "mountpoint",
            "replicaset",
            "release",
            "status",
            "deployment",
            "statefulset",
        ]
        extra_fields = {}
        for field in fields:
            field_value = self.data.get("labels", {}).get(field)
            if field_value:
                extra_fields[field] = field_value
        return extra_fields

    def can_send_notification(self, channel: str) -> bool:
        def match(value, filter):
            if not value or not filter:
                return True
            operator = "~" if filter[0] == "~" else "="
            if filter[0] in ["=", "~"]:
                filter = filter[1:]
            return (operator == "=" and filter.lower() == value.lower()) or (
                operator == "~" and re.search(filter, value)
            )

        if self.cluster.upgrade_in_progress:
            return False

        if self.cluster.alert_system_settings:
            # Don't send notifications for certain pre-configured conditions
            for condition in self.cluster.alert_system_settings.get(
                "muted_notifications", []
            ):
                # TODO: Extend to support more attributes and operators
                namespace_match = match(self.namespace, condition.get("namespace"))
                pod_match = match(
                    self.data.get("labels", {}).get("pod"),
                    condition.get("pod"),
                )
                name_match = match(self.name, condition.get("name"))
                channel_match = match(channel, condition.get("channel"))
                if namespace_match and pod_match and name_match and channel_match:
                    return False
        return True

    def generate_notifications(self):
        metadata = self.generate_metadata()
        path = reverse("admin:clusters_clusteralert_change", args=(self.id,))
        link = f"https://api.{self.cluster.domain}{path}"

        if self.can_send_notification("sentry"):
            with sentry_sdk.push_scope() as scope:
                scope.set_tag(
                    "cluster_namespace",
                    f"{metadata['namespace']} [{self.cluster.domain}]",
                )
                scope.set_tag("issue_type", "cluster_alert")
                if self.environment:
                    scope.set_tag(
                        "account",
                        f"{self.environment.project.account.name} [{self.cluster.domain}]",
                    )
                    scope.set_tag(
                        "env",
                        f"{self.environment.name} ({self.environment.slug}) [{self.cluster.domain}]",
                    )
                    scope.set_tag("env_type", self.environment.type)
                    scope.set_tag(
                        "project",
                        f"{self.environment.project.name} ({self.environment.project.slug}) [{self.cluster.domain}]",
                    )
                scope.set_extra("alert_link", link)

                level = "info" if metadata["severity"] == "warning" else "error"
                sentry_sdk.capture_message(self.summary, level)

        if not self.is_system_alert():
            account_notification = AccountNotification(
                cluster_alert=self,
                environment=self.environment,
                account=self.environment.account,
                title=f"Account alert: {self.name} on environment: {self.environment.name}",
                body=self.summary,
                kind=AccountNotification.KIND_CLUSTER,
            )
            extra_fields = self.generate_extra_fields()
            date_format = "%a, %d %b %Y %H:%M:%S (%Z)"
            metadata["started_at"] = metadata["started_at"].strftime(date_format)
            if "ended_at" in metadata:
                metadata["ended_at"] = metadata["ended_at"].strftime(date_format)
            metadata.update(extra_fields)
            account_notification.set_slack_data(metadata)
            account_notification.set_slack_link("More details", link)
            account_notification.save(send_on_save=True)

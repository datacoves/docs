import logging
from datetime import datetime

from django.http import Http404, JsonResponse
from django.utils.timezone import make_aware
from projects.models import Environment
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from lib.tools import get_related_environment

from .builder import WorkbenchBuilder
from .models import Cluster, ClusterAlert

logger = logging.getLogger(__name__)


def healthcheck(request):
    return JsonResponse({"status": "ok"})


class WorkbenchStatus(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, environment_slug):
        try:
            status = (
                WorkbenchBuilder(request.user, environment_slug)
                .check_permissions()
                .status.check_status()
                .build()
            )

            if status is None:
                return Response(status=HTTP_200_OK)

            return Response(status, status=HTTP_200_OK)

        except Environment.DoesNotExist:
            raise Http404()


class WorkbenchHeartbeat(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, environment_slug):
        try:
            WorkbenchBuilder(
                request.user, environment_slug
            ).check_permissions().heartbeat().build()
            return Response(status=HTTP_200_OK)

        except Environment.DoesNotExist:
            raise Http404()


class WorkbenchCodeServerRestart(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, environment_slug):
        try:
            WorkbenchBuilder(
                request.user, environment_slug
            ).check_permissions().code_server.restart().build()
            return Response(status=HTTP_200_OK)

        except Environment.DoesNotExist:
            raise Http404()


class WorkbenchCodeServerStartLocalAirflow(views.APIView):
    permission_classes = [IsAuthenticated]

    def has_permission(self, request, view):
        """Add in check for user being one of the sys admins of the project
        or environment"""
        user = request.user
        env_slug = request.environment_slug
        env = WorkbenchBuilder(request.user, env_slug).set_environment().environment

        return (
            super().has_permission(request, view)
            and len(user.service_resource_permissions("airflow:admin", env)) > 0
        )

    def post(self, request, environment_slug):
        """Enable and start local airflow"""
        try:
            WorkbenchBuilder(
                request.user, environment_slug
            ).check_permissions().code_server.enable_local_airflow().build()
            return Response(status=HTTP_200_OK)

        except Environment.DoesNotExist:
            raise Http404()


class WorkbenchCodeServerSettings(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, environment_slug):
        try:
            WorkbenchBuilder(
                request.user, environment_slug
            ).check_permissions().code_server.update_settings(request.data).build()
            return Response(status=HTTP_200_OK)

        except Environment.DoesNotExist:
            raise Http404()

    def get(self, request, environment_slug):
        try:
            ue = (
                WorkbenchBuilder(request.user, environment_slug)
                .check_permissions()
                .code_server.build()
            )
            return Response(ue.code_server_config, status=HTTP_200_OK)

        except Environment.DoesNotExist:
            raise Http404()


class AlertView(views.APIView):
    def post(self, request, *args, **kwargs):
        cluster = Cluster.objects.current().first()
        alerts = request.data.pop("alerts")
        for alert_payload in alerts:
            self.process_alert(alert_payload, cluster)
        return Response(data={}, status=status.HTTP_200_OK)

    def process_alert(self, alert_payload, cluster):
        status = alert_payload.get("status")
        name = alert_payload.get("labels", {}).get("alertname", None)
        alert_type = alert_payload.get("labels", {}).get("alert_type", None)
        date = alert_payload["startsAt"]
        if alert_type == "log":
            # Loki Logs alerts have a different format than others.
            # We need to truncate milliseconds to 6 digits
            date = date[:-4] + "Z"
        resolved = status == "resolved"
        started_at = make_aware(datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ"))
        namespace = alert_payload.get("labels", {}).get("namespace", None)
        environment = get_related_environment(namespace) if namespace else None

        previous_alerts = ClusterAlert.objects.filter(
            name=name,
            namespace=namespace,
            cluster=cluster,
            environment=environment,
            resolved=False,
            started_at=started_at,
        )
        exists = previous_alerts.exists()
        if not resolved and not exists:
            alert = ClusterAlert.objects.create(
                data=alert_payload,
                cluster=cluster,
                name=name,
                namespace=namespace,
                environment=environment,
                status=status,
                resolved=resolved,
                started_at=started_at,
            )
            alert.generate_notifications()
        elif exists:
            previous_alerts.update(resolved=True)

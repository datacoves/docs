from datetime import timedelta
from unittest.mock import patch

from clusters.models import Cluster, ClusterAlert
from clusters.tasks import delete_cluster_alerts_older
from django.test import TestCase
from django.utils import timezone
from projects.models import Release


class KubectlMock:
    """Mock class to Kubectl client"""

    def get_ingress_controller_ips(self):
        return "10.0.0.10", "192.168.100.10"

    def get_cluster_apiserver_ips(self):
        return {}


class TestDeleteClusterAlertsOlder(TestCase):
    @patch("lib.kubernetes.client.Kubectl")
    def setUp(self, mock_k8s_client) -> None:
        mock_k8s_client.return_value = KubectlMock()

        release = Release.objects.create(
            name="Release dummy",
            commit="123456",
            released_at=timezone.now(),
        )

        cluster = Cluster.objects.create(
            domain="datacoveslocal.com", kubernetes_version="1.27", release=release
        )

        for i in range(0, 100):
            ClusterAlert.objects.create(
                started_at=timezone.now(),
                name=f"Example {i + 1}",
                cluster=cluster,
                status="Resolved",
                data={},
            )

        # Force specific created_at for test
        created_at = self.get_datetime_days_ago(days_ago=15)
        for cluster_alert in ClusterAlert.objects.all()[:50]:
            cluster_alert.created_at = created_at
            cluster_alert.save()

    def get_datetime_days_ago(self, days_ago):
        """Return datetime by days"""
        return timezone.now() - timedelta(days=days_ago)

    def test_deleted_by_two_weeks_ago(self):
        """Test task to delete ClusterAlerts older by days with task"""
        regs = ClusterAlert.objects.count()
        self.assertEqual(100, regs)

        result = delete_cluster_alerts_older(days_ago=14)
        regs = ClusterAlert.objects.count()

        self.assertIn("ClusterAlerts deleted [50]", result)
        self.assertEqual(50, regs)

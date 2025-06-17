from unittest.mock import patch

from clusters.adapters.code_server import CodeServerAdapter
from clusters.models.cluster import Cluster
from django.test import TestCase
from dotmap import DotMap
from factories import ClusterFactory, EnvironmentFactory, ProjectFactory

NODE_MEMORY_GIGABYTE = 16


class CeleryInspectMock:
    """Mock class to Celery Inspect"""

    def reserved(self):
        return {}


class NodeListMock:
    @property
    def items(self):
        return [
            DotMap(
                {
                    "status": {
                        "capacity": {
                            "cpu": "10",
                            "memory": f"{NODE_MEMORY_GIGABYTE}Gi",
                            "pods": "110",
                        }
                    }
                }
            )
        ]


class KubectlMock:
    def get_ingress_controller_ips(self):
        return "10.0.0.10", "192.168.100.10"

    def get_cluster_apiserver_ips(self):
        return {}

    def get_nodes_by_selector(self, selector):
        return NodeListMock()


class CodeServerResourceTest(TestCase):
    def setUp(self):
        self.project = ProjectFactory.create()
        self.services = {
            "code-server": {"valid": True, "enabled": True, "unmet_preconditions": []},
        }
        self.internal_services = {}

    def create_cluster(self, mock_cluster, cluster_provider):
        cluster = ClusterFactory.create(
            provider=cluster_provider,
            code_server_config={"overprovisioning": {"enabled": False}},
        )

        return cluster

    @patch("lib.kubernetes.client.Kubectl", return_value=KubectlMock())
    @patch("datacoves.celery.app.control.inspect", return_value=CeleryInspectMock())
    def test_code_server_resource_on_aks(self, mock_cluster, mock_celery_inspect):
        env = EnvironmentFactory.create(
            cluster=self.create_cluster(mock_cluster, Cluster.AKS_PROVIDER),
            project=self.project,
            services=self.services,
            internal_services=self.internal_services,
        )

        max_pods_by_node = 8  # AKS
        request_memory = int(NODE_MEMORY_GIGABYTE / max_pods_by_node * 1024)

        env.code_server_config = CodeServerAdapter.get_cluster_default_config(
            cluster=env.cluster
        )
        resources = CodeServerAdapter.gen_resources(env=env)
        code_server_config = env.code_server_config
        self.assertIsNotNone(resources)
        self.assertEqual(
            code_server_config["max_code_server_pods_per_node"], max_pods_by_node
        )
        self.assertEqual(
            code_server_config["resources"]["requests"]["memory"], f"{request_memory}Mi"
        )

    @patch("lib.kubernetes.client.Kubectl", return_value=KubectlMock())
    @patch("datacoves.celery.app.control.inspect", return_value=CeleryInspectMock())
    def test_code_server_resource_on_eks(self, mock_cluster, mock_celery_inspect):
        env = EnvironmentFactory.create(
            cluster=self.create_cluster(mock_cluster, Cluster.EKS_PROVIDER),
            project=self.project,
            services=self.services,
            internal_services=self.internal_services,
        )

        max_pods_by_node = 16  # EKS
        request_memory = int(NODE_MEMORY_GIGABYTE / max_pods_by_node * 1024)

        env.code_server_config = CodeServerAdapter.get_cluster_default_config(
            cluster=env.cluster
        )
        resources = CodeServerAdapter.gen_resources(env=env)
        code_server_config = env.code_server_config
        self.assertIsNotNone(resources)
        self.assertEqual(
            code_server_config["max_code_server_pods_per_node"], max_pods_by_node
        )
        self.assertEqual(
            code_server_config["resources"]["requests"]["memory"], f"{request_memory}Mi"
        )

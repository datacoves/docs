import datetime
import logging
from functools import cached_property

import kubernetes.client as kclient
import kubernetes.client.api as kapi
import kubernetes.config as kconfig
from kubernetes.client.exceptions import ApiException

# fmt: off
DISPATCH_CREATE = {
    ('v1', 'Binding'): ('CoreV1Api', 'create_namespaced_binding', True),  # noqa
    ('v1', 'ConfigMap'): ('CoreV1Api', 'create_namespaced_config_map', True),  # noqa
    ('v1', 'Endpoints'): ('CoreV1Api', 'create_namespaced_endpoints', True),  # noqa
    ('v1', 'Event'): ('CoreV1Api', 'create_namespaced_event', True),  # noqa
    ('v1', 'LimitRange'): ('CoreV1Api', 'create_namespaced_limit_range', True),  # noqa
    ('v1', 'Namespace'): ('CoreV1Api', 'create_namespace', False),  # noqa
    ('v1', 'Node'): ('CoreV1Api', 'create_node', False),  # noqa
    ('v1', 'PersistentVolumeClaim'): ('CoreV1Api', 'create_namespaced_persistent_volume_claim', True),  # noqa
    ('v1', 'PersistentVolume'): ('CoreV1Api', 'create_persistent_volume', False),  # noqa
    ('v1', 'Pod'): ('CoreV1Api', 'create_namespaced_pod', True),  # noqa
    ('v1', 'PodTemplate'): ('CoreV1Api', 'create_namespaced_pod_template', True),  # noqa
    ('v1', 'ReplicationController'): ('CoreV1Api', 'create_namespaced_replication_controller', True),  # noqa
    ('v1', 'ResourceQuota'): ('CoreV1Api', 'create_namespaced_resource_quota', True),  # noqa
    ('v1', 'Secret'): ('CoreV1Api', 'create_namespaced_secret', True),  # noqa
    ('v1', 'ServiceAccount'): ('CoreV1Api', 'create_namespaced_service_account', True),  # noqa
    ('v1', 'Service'): ('CoreV1Api', 'create_namespaced_service', True),  # noqa
    ('admissionregistration.k8s.io/v1', 'MutatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'create_mutating_webhook_configuration', False),  # noqa
    ('admissionregistration.k8s.io/v1', 'ValidatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'create_validating_webhook_configuration', False),  # noqa
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition'): ('ApiextensionsV1Api', 'create_custom_resource_definition', False),  # noqa
    ('apiregistration.k8s.io/v1', 'APIService'): ('ApiregistrationV1Api', 'create_api_service', False),  # noqa
    ('apps/v1', 'ControllerRevision'): ('AppsV1Api', 'create_namespaced_controller_revision', True),  # noqa
    ('apps/v1', 'DaemonSet'): ('AppsV1Api', 'create_namespaced_daemon_set', True),  # noqa
    ('apps/v1', 'Deployment'): ('AppsV1Api', 'create_namespaced_deployment', True),  # noqa
    ('apps/v1', 'ReplicaSet'): ('AppsV1Api', 'create_namespaced_replica_set', True),  # noqa
    ('apps/v1', 'StatefulSet'): ('AppsV1Api', 'create_namespaced_stateful_set', True),  # noqa
    ('authentication.k8s.io/v1', 'TokenReview'): ('AuthenticationV1Api', 'create_token_review', False),  # noqa
    ('authorization.k8s.io/v1', 'LocalSubjectAccessReview'): ('AuthorizationV1Api', 'create_namespaced_local_subject_access_review', True),  # noqa
    ('authorization.k8s.io/v1', 'SelfSubjectAccessReview'): ('AuthorizationV1Api', 'create_self_subject_access_review', False),  # noqa
    ('authorization.k8s.io/v1', 'SelfSubjectRulesReview'): ('AuthorizationV1Api', 'create_self_subject_rules_review', False),  # noqa
    ('authorization.k8s.io/v1', 'SubjectAccessReview'): ('AuthorizationV1Api', 'create_subject_access_review', False),  # noqa
    ('batch/v1', 'CronJob'): ('BatchV1Api', 'create_namespaced_cron_job', True),  # noqa
    ('batch/v1', 'Job'): ('BatchV1Api', 'create_namespaced_job', True),  # noqa
    ('certificates.k8s.io/v1', 'CertificateSigningRequest'): ('CertificatesV1Api', 'create_certificate_signing_request', False),  # noqa
    ('coordination.k8s.io/v1', 'Lease'): ('CoordinationV1Api', 'create_namespaced_lease', True),  # noqa
    ('events.k8s.io/v1', 'Event'): ('EventsV1Api', 'create_namespaced_event', True),  # noqa
    ('networking.k8s.io/v1', 'IngressClass'): ('NetworkingV1Api', 'create_ingress_class', False),  # noqa
    ('networking.k8s.io/v1', 'Ingress'): ('NetworkingV1Api', 'create_namespaced_ingress', True),  # noqa
    ('networking.k8s.io/v1', 'NetworkPolicy'): ('NetworkingV1Api', 'create_namespaced_network_policy', True),  # noqa
    ('node.k8s.io/v1', 'RuntimeClass'): ('NodeV1Api', 'create_runtime_class', False),  # noqa
    ('policy/v1beta1', 'PodSecurityPolicy'): ('PolicyV1beta1Api', 'create_pod_security_policy', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRoleBinding'): ('RbacAuthorizationV1Api', 'create_cluster_role_binding', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRole'): ('RbacAuthorizationV1Api', 'create_cluster_role', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'RoleBinding'): ('RbacAuthorizationV1Api', 'create_namespaced_role_binding', True),  # noqa
    ('rbac.authorization.k8s.io/v1', 'Role'): ('RbacAuthorizationV1Api', 'create_namespaced_role', True),  # noqa
    ('scheduling.k8s.io/v1', 'PriorityClass'): ('SchedulingV1Api', 'create_priority_class', False),  # noqa
    ('storage.k8s.io/v1', 'CSIDriver'): ('StorageV1Api', 'create_csi_driver', False),  # noqa
    ('storage.k8s.io/v1', 'CSINode'): ('StorageV1Api', 'create_csi_node', False),  # noqa
    ('storage.k8s.io/v1beta1', 'CSIStorageCapacity'): ('StorageV1beta1Api', 'create_namespaced_csi_storage_capacity', True),  # noqa
    ('storage.k8s.io/v1', 'StorageClass'): ('StorageV1Api', 'create_storage_class', False),  # noqa
    ('storage.k8s.io/v1', 'VolumeAttachment'): ('StorageV1Api', 'create_volume_attachment', False),  # noqa
    ('datacoves.com/v1', 'Account'): ('DatacovesApi', 'create_namespaced_account', True),  # noqa
    ('datacoves.com/v1', 'HelmRelease'): ('DatacovesApi', 'create_namespaced_helm_release', True),  # noqa
    ('datacoves.com/v1', 'User'): ('DatacovesApi', 'create_namespaced_user', True),  # noqa
    ('datacoves.com/v1', 'Workspace'): ('DatacovesApi', 'create_namespaced_workspace', True),  # noqa
    ('monitoring.coreos.com/v1', 'ServiceMonitor'): ('MonitoringCoreosComV1Api', 'create_namespaced_service_monitor', True),  # noqa
}
DISPATCH_READ = {
    ('v1', 'ComponentStatus'): ('CoreV1Api', 'read_component_status', False),  # noqa
    ('v1', 'ConfigMap'): ('CoreV1Api', 'read_namespaced_config_map', True),  # noqa
    ('v1', 'Endpoints'): ('CoreV1Api', 'read_namespaced_endpoints', True),  # noqa
    ('v1', 'Event'): ('CoreV1Api', 'read_namespaced_event', True),  # noqa
    ('v1', 'LimitRange'): ('CoreV1Api', 'read_namespaced_limit_range', True),  # noqa
    ('v1', 'Namespace'): ('CoreV1Api', 'read_namespace', False),  # noqa
    ('v1', 'Node'): ('CoreV1Api', 'read_node', False),  # noqa
    ('v1', 'PersistentVolumeClaim'): ('CoreV1Api', 'read_namespaced_persistent_volume_claim', True),  # noqa
    ('v1', 'PersistentVolume'): ('CoreV1Api', 'read_persistent_volume', False),  # noqa
    ('v1', 'Pod'): ('CoreV1Api', 'read_namespaced_pod', True),  # noqa
    ('v1', 'PodTemplate'): ('CoreV1Api', 'read_namespaced_pod_template', True),  # noqa
    ('v1', 'ReplicationController'): ('CoreV1Api', 'read_namespaced_replication_controller', True),  # noqa
    ('v1', 'ResourceQuota'): ('CoreV1Api', 'read_namespaced_resource_quota', True),  # noqa
    ('v1', 'Secret'): ('CoreV1Api', 'read_namespaced_secret', True),  # noqa
    ('v1', 'ServiceAccount'): ('CoreV1Api', 'read_namespaced_service_account', True),  # noqa
    ('v1', 'Service'): ('CoreV1Api', 'read_namespaced_service', True),  # noqa
    ('admissionregistration.k8s.io/v1', 'MutatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'read_mutating_webhook_configuration', False),  # noqa
    ('admissionregistration.k8s.io/v1', 'ValidatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'read_validating_webhook_configuration', False),  # noqa
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition'): ('ApiextensionsV1Api', 'read_custom_resource_definition', False),  # noqa
    ('apiregistration.k8s.io/v1', 'APIService'): ('ApiregistrationV1Api', 'read_api_service', False),  # noqa
    ('apps/v1', 'ControllerRevision'): ('AppsV1Api', 'read_namespaced_controller_revision', True),  # noqa
    ('apps/v1', 'DaemonSet'): ('AppsV1Api', 'read_namespaced_daemon_set', True),  # noqa
    ('apps/v1', 'Deployment'): ('AppsV1Api', 'read_namespaced_deployment', True),  # noqa
    ('apps/v1', 'ReplicaSet'): ('AppsV1Api', 'read_namespaced_replica_set', True),  # noqa
    ('apps/v1', 'StatefulSet'): ('AppsV1Api', 'read_namespaced_stateful_set', True),  # noqa
    ('batch/v1', 'CronJob'): ('BatchV1Api', 'read_namespaced_cron_job', True),  # noqa
    ('batch/v1', 'Job'): ('BatchV1Api', 'read_namespaced_job', True),  # noqa
    ('certificates.k8s.io/v1', 'CertificateSigningRequest'): ('CertificatesV1Api', 'read_certificate_signing_request', False),  # noqa
    ('coordination.k8s.io/v1', 'Lease'): ('CoordinationV1Api', 'read_namespaced_lease', True),  # noqa
    ('events.k8s.io/v1', 'Event'): ('EventsV1Api', 'read_namespaced_event', True),  # noqa
    ('networking.k8s.io/v1', 'IngressClass'): ('NetworkingV1Api', 'read_ingress_class', False),  # noqa
    ('networking.k8s.io/v1', 'Ingress'): ('NetworkingV1Api', 'read_namespaced_ingress', True),  # noqa
    ('networking.k8s.io/v1', 'NetworkPolicy'): ('NetworkingV1Api', 'read_namespaced_network_policy', True),  # noqa
    ('node.k8s.io/v1', 'RuntimeClass'): ('NodeV1Api', 'read_runtime_class', False),  # noqa
    ('policy/v1beta1', 'PodSecurityPolicy'): ('PolicyV1beta1Api', 'read_pod_security_policy', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRoleBinding'): ('RbacAuthorizationV1Api', 'read_cluster_role_binding', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRole'): ('RbacAuthorizationV1Api', 'read_cluster_role', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'RoleBinding'): ('RbacAuthorizationV1Api', 'read_namespaced_role_binding', True),  # noqa
    ('rbac.authorization.k8s.io/v1', 'Role'): ('RbacAuthorizationV1Api', 'read_namespaced_role', True),  # noqa
    ('scheduling.k8s.io/v1', 'PriorityClass'): ('SchedulingV1Api', 'read_priority_class', False),  # noqa
    ('storage.k8s.io/v1', 'CSIDriver'): ('StorageV1Api', 'read_csi_driver', False),  # noqa
    ('storage.k8s.io/v1', 'CSINode'): ('StorageV1Api', 'read_csi_node', False),  # noqa
    ('storage.k8s.io/v1beta1', 'CSIStorageCapacity'): ('StorageV1beta1Api', 'read_namespaced_csi_storage_capacity', True),  # noqa
    ('storage.k8s.io/v1', 'StorageClass'): ('StorageV1Api', 'read_storage_class', False),  # noqa
    ('storage.k8s.io/v1', 'VolumeAttachment'): ('StorageV1Api', 'read_volume_attachment', False),  # noqa
    ('datacoves.com/v1', 'Account'): ('DatacovesApi', 'read_namespaced_account', True),  # noqa
    ('datacoves.com/v1', 'HelmRelease'): ('DatacovesApi', 'read_namespaced_helm_release', True),  # noqa
    ('datacoves.com/v1', 'User'): ('DatacovesApi', 'read_namespaced_user', True),  # noqa
    ('datacoves.com/v1', 'Workspace'): ('DatacovesApi', 'read_namespaced_workspace', True),  # noqa
    ('monitoring.coreos.com/v1', 'ServiceMonitor'): ('MonitoringCoreosComV1Api', 'read_namespaced_service_monitor', True),  # noqa
}
DISPATCH_REPLACE = {
    ('v1', 'ConfigMap'): ('CoreV1Api', 'replace_namespaced_config_map', True),  # noqa
    ('v1', 'Endpoints'): ('CoreV1Api', 'replace_namespaced_endpoints', True),  # noqa
    ('v1', 'Event'): ('CoreV1Api', 'replace_namespaced_event', True),  # noqa
    ('v1', 'LimitRange'): ('CoreV1Api', 'replace_namespaced_limit_range', True),  # noqa
    ('v1', 'Namespace'): ('CoreV1Api', 'replace_namespace', False),  # noqa
    ('v1', 'Node'): ('CoreV1Api', 'replace_node', False),  # noqa
    ('v1', 'PersistentVolumeClaim'): ('CoreV1Api', 'replace_namespaced_persistent_volume_claim', True),  # noqa
    ('v1', 'PersistentVolume'): ('CoreV1Api', 'replace_persistent_volume', False),  # noqa
    ('v1', 'Pod'): ('CoreV1Api', 'replace_namespaced_pod', True),  # noqa
    ('v1', 'PodTemplate'): ('CoreV1Api', 'replace_namespaced_pod_template', True),  # noqa
    ('v1', 'ReplicationController'): ('CoreV1Api', 'replace_namespaced_replication_controller', True),  # noqa
    ('v1', 'ResourceQuota'): ('CoreV1Api', 'replace_namespaced_resource_quota', True),  # noqa
    ('v1', 'Secret'): ('CoreV1Api', 'replace_namespaced_secret', True),  # noqa
    ('v1', 'ServiceAccount'): ('CoreV1Api', 'replace_namespaced_service_account', True),  # noqa
    ('v1', 'Service'): ('CoreV1Api', 'replace_namespaced_service', True),  # noqa
    ('admissionregistration.k8s.io/v1', 'MutatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'replace_mutating_webhook_configuration', False),  # noqa
    ('admissionregistration.k8s.io/v1', 'ValidatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'replace_validating_webhook_configuration', False),  # noqa
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition'): ('ApiextensionsV1Api', 'replace_custom_resource_definition', False),  # noqa
    ('apiregistration.k8s.io/v1', 'APIService'): ('ApiregistrationV1Api', 'replace_api_service', False),  # noqa
    ('apps/v1', 'ControllerRevision'): ('AppsV1Api', 'replace_namespaced_controller_revision', True),  # noqa
    ('apps/v1', 'DaemonSet'): ('AppsV1Api', 'replace_namespaced_daemon_set', True),  # noqa
    ('apps/v1', 'Deployment'): ('AppsV1Api', 'replace_namespaced_deployment', True),  # noqa
    ('apps/v1', 'ReplicaSet'): ('AppsV1Api', 'replace_namespaced_replica_set', True),  # noqa
    ('apps/v1', 'StatefulSet'): ('AppsV1Api', 'replace_namespaced_stateful_set', True),  # noqa
    ('batch/v1', 'CronJob'): ('BatchV1Api', 'replace_namespaced_cron_job', True),  # noqa
    ('batch/v1', 'Job'): ('BatchV1Api', 'replace_namespaced_job', True),  # noqa
    ('certificates.k8s.io/v1', 'CertificateSigningRequest'): ('CertificatesV1Api', 'replace_certificate_signing_request', False),  # noqa
    ('coordination.k8s.io/v1', 'Lease'): ('CoordinationV1Api', 'replace_namespaced_lease', True),  # noqa
    ('events.k8s.io/v1', 'Event'): ('EventsV1Api', 'replace_namespaced_event', True),  # noqa
    ('networking.k8s.io/v1', 'IngressClass'): ('NetworkingV1Api', 'replace_ingress_class', False),  # noqa
    ('networking.k8s.io/v1', 'Ingress'): ('NetworkingV1Api', 'replace_namespaced_ingress', True),  # noqa
    ('networking.k8s.io/v1', 'NetworkPolicy'): ('NetworkingV1Api', 'replace_namespaced_network_policy', True),  # noqa
    ('node.k8s.io/v1', 'RuntimeClass'): ('NodeV1Api', 'replace_runtime_class', False),  # noqa
    ('policy/v1beta1', 'PodSecurityPolicy'): ('PolicyV1beta1Api', 'replace_pod_security_policy', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRoleBinding'): ('RbacAuthorizationV1Api', 'replace_cluster_role_binding', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRole'): ('RbacAuthorizationV1Api', 'replace_cluster_role', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'RoleBinding'): ('RbacAuthorizationV1Api', 'replace_namespaced_role_binding', True),  # noqa
    ('rbac.authorization.k8s.io/v1', 'Role'): ('RbacAuthorizationV1Api', 'replace_namespaced_role', True),  # noqa
    ('scheduling.k8s.io/v1', 'PriorityClass'): ('SchedulingV1Api', 'replace_priority_class', False),  # noqa
    ('storage.k8s.io/v1', 'CSIDriver'): ('StorageV1Api', 'replace_csi_driver', False),  # noqa
    ('storage.k8s.io/v1', 'CSINode'): ('StorageV1Api', 'replace_csi_node', False),  # noqa
    ('storage.k8s.io/v1beta1', 'CSIStorageCapacity'): ('StorageV1beta1Api', 'replace_namespaced_csi_storage_capacity', True),  # noqa
    ('storage.k8s.io/v1', 'StorageClass'): ('StorageV1Api', 'replace_storage_class', False),  # noqa
    ('storage.k8s.io/v1', 'VolumeAttachment'): ('StorageV1Api', 'replace_volume_attachment', False),  # noqa
    ('datacoves.com/v1', 'Account'): ('DatacovesApi', 'replace_namespaced_account', True),  # noqa
    ('datacoves.com/v1', 'HelmRelease'): ('DatacovesApi', 'replace_namespaced_helm_release', True),  # noqa
    ('datacoves.com/v1', 'User'): ('DatacovesApi', 'replace_namespaced_user', True),  # noqa
    ('datacoves.com/v1', 'Workspace'): ('DatacovesApi', 'replace_namespaced_workspace', True),  # noqa
    ('monitoring.coreos.com/v1', 'ServiceMonitor'): ('MonitoringCoreosComV1Api', 'replace_namespaced_service_monitor', True),  # noqa
}
DISPATCH_DELETE = {
    ('v1', 'ConfigMap'): ('CoreV1Api', 'delete_namespaced_config_map', True),  # noqa
    ('v1', 'Endpoints'): ('CoreV1Api', 'delete_namespaced_endpoints', True),  # noqa
    ('v1', 'Event'): ('CoreV1Api', 'delete_namespaced_event', True),  # noqa
    ('v1', 'LimitRange'): ('CoreV1Api', 'delete_namespaced_limit_range', True),  # noqa
    ('v1', 'Namespace'): ('CoreV1Api', 'delete_namespace', False),  # noqa
    ('v1', 'Node'): ('CoreV1Api', 'delete_node', False),  # noqa
    ('v1', 'PersistentVolumeClaim'): ('CoreV1Api', 'delete_namespaced_persistent_volume_claim', True),  # noqa
    ('v1', 'PersistentVolume'): ('CoreV1Api', 'delete_persistent_volume', False),  # noqa
    ('v1', 'Pod'): ('CoreV1Api', 'delete_namespaced_pod', True),  # noqa
    ('v1', 'PodTemplate'): ('CoreV1Api', 'delete_namespaced_pod_template', True),  # noqa
    ('v1', 'ReplicationController'): ('CoreV1Api', 'delete_namespaced_replication_controller', True),  # noqa
    ('v1', 'ResourceQuota'): ('CoreV1Api', 'delete_namespaced_resource_quota', True),  # noqa
    ('v1', 'Secret'): ('CoreV1Api', 'delete_namespaced_secret', True),  # noqa
    ('v1', 'ServiceAccount'): ('CoreV1Api', 'delete_namespaced_service_account', True),  # noqa
    ('v1', 'Service'): ('CoreV1Api', 'delete_namespaced_service', True),  # noqa
    ('admissionregistration.k8s.io/v1', 'MutatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'delete_mutating_webhook_configuration', False),  # noqa
    ('admissionregistration.k8s.io/v1', 'ValidatingWebhookConfiguration'): ('AdmissionregistrationV1Api', 'delete_validating_webhook_configuration', False),  # noqa
    ('apiextensions.k8s.io/v1', 'CustomResourceDefinition'): ('ApiextensionsV1Api', 'delete_custom_resource_definition', False),  # noqa
    ('apiregistration.k8s.io/v1', 'APIService'): ('ApiregistrationV1Api', 'delete_api_service', False),  # noqa
    ('apps/v1', 'ControllerRevision'): ('AppsV1Api', 'delete_namespaced_controller_revision', True),  # noqa
    ('apps/v1', 'DaemonSet'): ('AppsV1Api', 'delete_namespaced_daemon_set', True),  # noqa
    ('apps/v1', 'Deployment'): ('AppsV1Api', 'delete_namespaced_deployment', True),  # noqa
    ('apps/v1', 'ReplicaSet'): ('AppsV1Api', 'delete_namespaced_replica_set', True),  # noqa
    ('apps/v1', 'StatefulSet'): ('AppsV1Api', 'delete_namespaced_stateful_set', True),  # noqa
    ('batch/v1', 'CronJob'): ('BatchV1Api', 'delete_namespaced_cron_job', True),  # noqa
    ('batch/v1', 'Job'): ('BatchV1Api', 'delete_namespaced_job', True),  # noqa
    ('certificates.k8s.io/v1', 'CertificateSigningRequest'): ('CertificatesV1Api', 'delete_certificate_signing_request', False),  # noqa
    ('coordination.k8s.io/v1', 'Lease'): ('CoordinationV1Api', 'delete_namespaced_lease', True),  # noqa
    ('events.k8s.io/v1', 'Event'): ('EventsV1Api', 'delete_namespaced_event', True),  # noqa
    ('networking.k8s.io/v1', 'IngressClass'): ('NetworkingV1Api', 'delete_ingress_class', False),  # noqa
    ('networking.k8s.io/v1', 'Ingress'): ('NetworkingV1Api', 'delete_namespaced_ingress', True),  # noqa
    ('networking.k8s.io/v1', 'NetworkPolicy'): ('NetworkingV1Api', 'delete_namespaced_network_policy', True),  # noqa
    ('node.k8s.io/v1', 'RuntimeClass'): ('NodeV1Api', 'delete_runtime_class', False),  # noqa
    ('policy/v1beta1', 'PodSecurityPolicy'): ('PolicyV1beta1Api', 'delete_pod_security_policy', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRoleBinding'): ('RbacAuthorizationV1Api', 'delete_cluster_role_binding', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'ClusterRole'): ('RbacAuthorizationV1Api', 'delete_cluster_role', False),  # noqa
    ('rbac.authorization.k8s.io/v1', 'RoleBinding'): ('RbacAuthorizationV1Api', 'delete_namespaced_role_binding', True),  # noqa
    ('rbac.authorization.k8s.io/v1', 'Role'): ('RbacAuthorizationV1Api', 'delete_namespaced_role', True),  # noqa
    ('scheduling.k8s.io/v1', 'PriorityClass'): ('SchedulingV1Api', 'delete_priority_class', False),  # noqa
    ('storage.k8s.io/v1', 'CSIDriver'): ('StorageV1Api', 'delete_csi_driver', False),  # noqa
    ('storage.k8s.io/v1', 'CSINode'): ('StorageV1Api', 'delete_csi_node', False),  # noqa
    ('storage.k8s.io/v1beta1', 'CSIStorageCapacity'): ('StorageV1beta1Api', 'delete_namespaced_csi_storage_capacity', True),  # noqa
    ('storage.k8s.io/v1', 'StorageClass'): ('StorageV1Api', 'delete_storage_class', False),  # noqa
    ('storage.k8s.io/v1', 'VolumeAttachment'): ('StorageV1Api', 'delete_volume_attachment', False),  # noqa
    ('datacoves.com/v1', 'Account'): ('DatacovesApi', 'delete_namespaced_account', True),  # noqa
    ('datacoves.com/v1', 'HelmRelease'): ('DatacovesApi', 'delete_namespaced_helm_release', True),  # noqa
    ('datacoves.com/v1', 'User'): ('DatacovesApi', 'delete_namespaced_user', True),  # noqa
    ('datacoves.com/v1', 'Workspace'): ('DatacovesApi', 'delete_namespaced_workspace', True),  # noqa
    ('monitoring.coreos.com/v1', 'ServiceMonitor'): ('MonitoringCoreosComV1Api', 'delete_namespaced_service_monitor', True),  # noqa
}
# fmt: on


class CustomDatacovesApi(object):
    def __init__(self, kc):
        self.kc = kc

    def create_namespaced_account(self, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.create_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "accounts", res, **kwargs
        )

    def read_namespaced_account(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.get_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "accounts", name, **kwargs
        )

    def replace_namespaced_account(self, name, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.replace_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "accounts", name, res, **kwargs
        )

    def delete_namespaced_account(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.delete_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "accounts", name, **kwargs
        )

    def create_namespaced_helm_release(self, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.create_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "helmreleases", res, **kwargs
        )

    def read_namespaced_helm_release(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.get_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "helmreleases", name, **kwargs
        )

    def replace_namespaced_helm_release(self, name, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.replace_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "helmreleases", name, res, **kwargs
        )

    def delete_namespaced_helm_release(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.delete_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "helmreleases", name, **kwargs
        )

    def create_namespaced_user(self, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.create_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "users", res, **kwargs
        )

    def read_namespaced_user(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.get_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "users", name, **kwargs
        )

    def replace_namespaced_user(self, name, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.replace_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "users", name, res, **kwargs
        )

    def delete_namespaced_user(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.delete_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "users", name, **kwargs
        )

    def create_namespaced_workspace(self, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.create_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "workspaces", res, **kwargs
        )

    def read_namespaced_workspace(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.get_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "workspaces", name, **kwargs
        )

    def replace_namespaced_workspace(self, name, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.replace_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "workspaces", name, res, **kwargs
        )

    def delete_namespaced_workspace(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.delete_namespaced_custom_object(
            "datacoves.com", "v1", namespace, "workspaces", name, **kwargs
        )


class CustomMonitoringCoreosComV1Api(object):
    def __init__(self, kc):
        self.kc = kc

    def create_namespaced_service_monitor(self, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.create_namespaced_custom_object(
            "monitoring.coreos.com", "v1", namespace, "servicemonitors", res, **kwargs
        )

    def read_namespaced_service_monitor(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.get_namespaced_custom_object(
            "monitoring.coreos.com", "v1", namespace, "servicemonitors", name, **kwargs
        )

    def replace_namespaced_service_monitor(self, name, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.replace_namespaced_custom_object(
            "monitoring.coreos.com",
            "v1",
            namespace,
            "servicemonitors",
            name,
            res,
            **kwargs,
        )

    def delete_namespaced_service_monitor(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.delete_namespaced_custom_object(
            "monitoring.coreos.com", "v1", namespace, "servicemonitors", name, **kwargs
        )


class CustomPolicyV1beta1Api(object):
    def __init__(self, kc):
        self.kc = kc


class CustomStorageV1beta1Api(object):
    def __init__(self, kc):
        self.kc = kc

    def create_namespaced_csi_storage_capacity(self, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.create_namespaced_custom_object(
            "storage.k8s.io", "v1beta1", namespace, "csistoragecapacitys", res, **kwargs
        )

    def read_namespaced_csi_storage_capacity(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.get_namespaced_custom_object(
            "storage.k8s.io",
            "v1beta1",
            namespace,
            "csistoragecapacitys",
            name,
            **kwargs,
        )

    def replace_namespaced_csi_storage_capacity(self, name, namespace, res, **kwargs):
        return self.kc.CustomObjectsApi.replace_namespaced_custom_object(
            "storage.k8s.io",
            "v1beta1",
            namespace,
            "csistoragecapacitys",
            name,
            res,
            **kwargs,
        )

    def delete_namespaced_csi_storage_capacity(self, name, namespace, **kwargs):
        return self.kc.CustomObjectsApi.delete_namespaced_custom_object(
            "storage.k8s.io",
            "v1beta1",
            namespace,
            "csistoragecapacitys",
            name,
            **kwargs,
        )


logger = logging.getLogger(__name__)


class Kubectl:
    def __init__(self, client=None, config=None, in_cluster=True):
        if not client:
            if not config:
                if in_cluster:
                    config = kconfig.load_incluster_config()
                else:
                    config = kconfig.load_kube_config()
            client = kclient.ApiClient(configuration=config)
        self.client = client

    def apply_resources(self, namespace, resources, log=None):
        for res in resources:
            ty = (res["apiVersion"], res["kind"])
            assert ty in DISPATCH_CREATE, f"unrecognized resource type: {ty}"
            namespaced = DISPATCH_CREATE[ty][2]
            if namespaced and res.get("metadata", {}).get("namespace") is None:
                res["metadata"]["namespace"] = namespace

        for res in resources:
            self.apply(res, log=log)

    def apply(self, resource, log=None):
        written, created, ret_obj = self.update_or_create(resource)

        if callable(log):
            api_version, kind, name = self.get_resource_metadata(resource)
            namespace = self.get_resource_namespace(resource)
            log(f"{'Created' if created else 'Updated'} {kind} {namespace}/{name}")

        return written, created, ret_obj

    def update_or_create(self, res, **kwargs):
        written, created = False, False
        obj = self.read(res, **kwargs)
        if obj is None:
            ret_obj = self.create(res, **kwargs)
            written = True
            created = True
            return written, created, ret_obj

        if hasattr(obj, "immutable"):
            return written, created, obj

        # We have to send the resourceVersion we got. If there's a modification in
        # between our GET and PUT, the PUT will fail.
        resource_version = (
            obj["metadata"]["resourceVersion"]
            if isinstance(obj, dict)
            else obj.metadata.resource_version
        )
        if isinstance(res, dict):
            res["metadata"]["resourceVersion"] = resource_version
        else:
            res.metadata.resource_version = resource_version

        ret_obj = self.replace(res, **kwargs)
        written = True
        return written, created, ret_obj

    def create(self, res, **kwargs):
        api_version, kind, _ = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_CREATE[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        namespace = self.get_resource_namespace(res) if namespaced else None
        return fn(namespace, res, **kwargs) if namespace else fn(res, **kwargs)

    def read(self, res, raise_404=False, **kwargs):
        api_version, kind, name = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_READ[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        try:
            namespace = self.get_resource_namespace(res) if namespaced else None
            return fn(name, namespace, **kwargs) if namespace else fn(name, **kwargs)
        except kclient.exceptions.ApiException as e:
            if raise_404 or e.status != 404:
                raise e
            return None

    def replace(self, res, **kwargs):
        api_version, kind, name = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_REPLACE[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        namespace = self.get_resource_namespace(res) if namespaced else None
        return (
            fn(name, namespace, res, **kwargs) if namespace else fn(name, res, **kwargs)
        )

    def delete(self, res, raise_404=False, **kwargs):
        api_version, kind, name = self.get_resource_metadata(res)
        api_class, f, namespaced = DISPATCH_DELETE[(api_version, kind)]
        api = getattr(self, api_class)
        fn = getattr(api, f)
        try:
            namespace = self.get_resource_namespace(res) if namespaced else None
            return fn(name, namespace, **kwargs) if namespace else fn(name, **kwargs)
        except kclient.exceptions.ApiException as e:
            if raise_404 or e.status != 404:
                raise e

    def get_resource_namespace(self, res) -> str:
        return (
            res["metadata"]["namespace"]
            if isinstance(res, dict)
            else res.metadata.namespace
        )

    def get_resource_metadata(self, res) -> tuple:
        if isinstance(res, dict):
            api_version = res["apiVersion"]
            kind = res["kind"]
            name = res["metadata"]["name"]
        else:
            api_version = res.api_version
            kind = res.kind
            name = res.metadata.name

            if api_version is None and isinstance(res, kclient.V1NetworkPolicy):
                api_version = "networking.k8s.io/v1"
                kind = "NetworkPolicy"

        return api_version, kind, name

    def get_cluster_apiserver_ips(self) -> dict:
        try:
            endpoints = self.CoreV1Api.read_namespaced_endpoints(
                namespace="default", name="kubernetes"
            )
            ips = []
            ports = []
            for subsets in endpoints.subsets:
                for address in subsets.addresses:
                    ips.append(address.ip)

                ports_filtered = filter(
                    lambda item: item.name == "https", subsets.ports
                )
                ports_aux = list(map(lambda item: item.port, ports_filtered))
                if ports_aux and ports_aux[0] not in ports:
                    ports.append(ports_aux[0])

            return {"ips": ips, "ports": ports}

        except Exception as e:
            logger.error("Cluster api server: %s", e.__str__())
            return {}

    def get_ingress_controller_ips(self):
        service = self.CoreV1Api.read_namespaced_service(
            "ingress-nginx-controller", "ingress-nginx"
        )
        internal_ip = service.spec.cluster_ip
        external_ip = None
        if service.spec.external_i_ps:
            external_ip = service.spec.external_i_ps[0]
        if not external_ip and service.status.load_balancer.ingress:
            external_ip = service.status.load_balancer.ingress[0].ip
        return internal_ip, external_ip

    def k8s_convert_selector_to_label_string(self, selector_dict: dict) -> str:
        if not isinstance(selector_dict, dict) or len(selector_dict) != 1:
            raise ValueError("Expected a dictionary with a single key-value pair.")

        return ",".join([f"{k}={v}" for k, v in selector_dict.items()])

    def get_nodes_by_selector(self, selector: dict[str, str]):
        return self.CoreV1Api.list_node(
            label_selector=self.k8s_convert_selector_to_label_string(selector)
        )

    def delete_namespace(self, namespace):
        return self.CoreV1Api.delete_namespace(namespace)

    def read_namespace(self, namespace):
        return self.CoreV1Api.read_namespace(namespace)

    def restart_deployment(self, deployment, namespace):
        try:
            now = datetime.datetime.now(datetime.UTC)
            now = str(now.isoformat("T") + "Z")
            body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {"kubectl.kubernetes.io/restartedAt": now}
                        }
                    }
                }
            }
            self.AppsV1Api.patch_namespaced_deployment(
                deployment, namespace, body, pretty="true"
            )
        except ApiException as e:
            if e.status != 404:
                raise

    def deployment_status_from_conditions(self, conditions):
        available = False
        progressing = False
        last_condition = None
        if conditions is not None:
            for condition in conditions:
                if condition.type == "Available" and condition.status == "True":
                    available = True
                elif condition.type == "Progressing" and condition.status == "True":
                    progressing = True
                last_condition = condition

        return {
            "available": available,
            "progressing": progressing,
            "condition": last_condition,
        }

    @cached_property
    def AdmissionregistrationV1Api(self):
        return kapi.AdmissionregistrationV1Api(api_client=self.client)

    @cached_property
    def ApiextensionsV1Api(self):
        return kapi.ApiextensionsV1Api(api_client=self.client)

    @cached_property
    def ApiregistrationV1Api(self):
        return kapi.ApiregistrationV1Api(api_client=self.client)

    @cached_property
    def AppsV1Api(self):
        return kapi.AppsV1Api(api_client=self.client)

    @cached_property
    def AuthenticationV1Api(self):
        return kapi.AuthenticationV1Api(api_client=self.client)

    @cached_property
    def AuthorizationV1Api(self):
        return kapi.AuthorizationV1Api(api_client=self.client)

    @cached_property
    def BatchV1Api(self):
        return kapi.BatchV1Api(api_client=self.client)

    @cached_property
    def CertificatesV1Api(self):
        return kapi.CertificatesV1Api(api_client=self.client)

    @cached_property
    def CoordinationV1Api(self):
        return kapi.CoordinationV1Api(api_client=self.client)

    @cached_property
    def CoreV1Api(self):
        return kapi.CoreV1Api(api_client=self.client)

    @cached_property
    def CustomObjectsApi(self):
        return kapi.CustomObjectsApi(api_client=self.client)

    @cached_property
    def EventsV1Api(self):
        return kapi.EventsV1Api(api_client=self.client)

    @cached_property
    def NetworkingV1Api(self):
        return kapi.NetworkingV1Api(api_client=self.client)

    @cached_property
    def NodeV1Api(self):
        return kapi.NodeV1Api(api_client=self.client)

    @cached_property
    def RbacAuthorizationV1Api(self):
        return kapi.RbacAuthorizationV1Api(api_client=self.client)

    @cached_property
    def SchedulingV1Api(self):
        return kapi.SchedulingV1Api(api_client=self.client)

    @cached_property
    def StorageV1Api(self):
        return kapi.StorageV1Api(api_client=self.client)

    @cached_property
    def DatacovesApi(self):
        return CustomDatacovesApi(kc=self)

    @cached_property
    def MonitoringCoreosComV1Api(self):
        return CustomMonitoringCoreosComV1Api(kc=self)

    @cached_property
    def PolicyV1beta1Api(self):
        return CustomPolicyV1beta1Api(kc=self)

    @cached_property
    def StorageV1beta1Api(self):
        return CustomStorageV1beta1Api(kc=self)

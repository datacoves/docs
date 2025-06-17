package controllers

import (
	"context"
	"strings"

	. "datacoves.com/operator/api/v1"
	core "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"sigs.k8s.io/controller-runtime/pkg/log"
)

func (r *WorkspaceReconciler) networkPolicies(ctx context.Context, workspace *Workspace) (err error) {
	log := log.FromContext(ctx)

	err = r.networkPoliciesDenyAll(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for Deny All")
		return
	}

	err = r.networkPoliciesAllowDNS(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for Allow DNS")
		return
	}

	err = r.networkPoliciesAllowInternet(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for Allow Internet")
		return
	}

	err = r.networkPoliciesWorkspaceIsolation(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for Namespace Isolation")
		return
	}

	err = r.networkPoliciesOpenPomerium(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for OpenPomerium")
		return
	}

	err = r.networkPolicyCodeServerToCoreApi(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for CodeServerToCoreApi")
		return
	}

	err = r.networkPolicyCodeServerToDbtApi(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for CodeServerToDbtApi")
		return
	}

	err = r.networkPolicyAirflowToCoreApi(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for AirflowToCoreApi")
		return
	}

	err = r.networkPolicyAirflowToDbtApi(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for AirflowToDbtApi")
		return
	}

	err = r.networkPolicyAllowIngressController(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies to access Ingress Controller")
		return
	}

	err = r.networkPoliciesAllowK8sApiServer(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies to access Ingress Controller")
		return
	}

	err = r.networkPolicyAirflowLogsToLokiGateway(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for Airflow Logs")
		return
	}

	err = r.networkPolicyDbtDocsToCoreApi(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for DBT Docs")
		return
	}

	err = r.networkPolicyAllowCrossEnvToSameProject(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: Network Policies for environmest in the same project")
		return
	}

	// This is only for local environment
	if strings.Contains(workspace.Spec.ClusterDomain, "datacoveslocal.com") {
		err = r.networkPolicyAllowLocalPostgres(ctx, workspace)
		if err != nil {
			log.Error(err, "error in stage: Network Policies for local Postgres")
			return
		}
	}

	return
}

func ptrProtocol(p core.Protocol) *core.Protocol {
	return &p
}

func (r *WorkspaceReconciler) networkPoliciesDenyAll(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyDenyAll(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyDenyAll(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "deny-all",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPoliciesAllowDNS(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyAllowDNS(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyAllowDNS(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-dns",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					Ports: []networkingv1.NetworkPolicyPort{
						{
							Protocol: ptrProtocol("UDP"),
							Port: &intstr.IntOrString{
								Type:   intstr.Type(0),
								IntVal: 53,
							},
						},
					},
					To: []networkingv1.NetworkPolicyPeer{
						{
							IPBlock: &networkingv1.IPBlock{
								CIDR: "0.0.0.0/0",
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPoliciesAllowInternet(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyAllowInternet(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyAllowInternet(workspace *Workspace) *networkingv1.NetworkPolicy {
	EgressRules := []networkingv1.NetworkPolicyPeer{
		{
			IPBlock: &networkingv1.IPBlock{
				CIDR: "0.0.0.0/0",
				Except: []string{
					"10.0.0.0/8",
					"192.168.0.0/16",
					"172.16.0.0/20",
				},
			},
		},
	}
	if workspace.Spec.InternalDnsIp != "" {
		EgressRules = append(EgressRules, networkingv1.NetworkPolicyPeer{
			IPBlock: &networkingv1.IPBlock{
				CIDR: workspace.Spec.InternalDnsIp + "/32",
			},
		})
	}
	if workspace.Spec.InternalDbClusterIpRange != "" {
		EgressRules = append(EgressRules, networkingv1.NetworkPolicyPeer{
			IPBlock: &networkingv1.IPBlock{
				CIDR: workspace.Spec.InternalDbClusterIpRange,
			},
		})
	}

	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-internet",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: EgressRules,
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPoliciesWorkspaceIsolation(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyWorkspaceIsolation(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyWorkspaceIsolation(workspace *Workspace) *networkingv1.NetworkPolicy {
	EgressRules := []networkingv1.NetworkPolicyPeer{
		{
			NamespaceSelector: &v1.LabelSelector{
				MatchLabels: map[string]string{
					"k8s.datacoves.com/workspace": workspace.Name,
				},
			},
		},
		{
			NamespaceSelector: &v1.LabelSelector{
				MatchLabels: map[string]string{
					"k8s.datacoves.com/account": workspace.Spec.Account,
				},
			},
		},
	}
	if workspace.Spec.InternalDnsIp != "" {
		EgressRules = append(EgressRules, networkingv1.NetworkPolicyPeer{
			IPBlock: &networkingv1.IPBlock{
				CIDR: workspace.Spec.InternalDnsIp + "/32",
			},
		})
	}
	if workspace.Spec.InternalDbClusterIpRange != "" {
		EgressRules = append(EgressRules, networkingv1.NetworkPolicyPeer{
			IPBlock: &networkingv1.IPBlock{
				CIDR: workspace.Spec.InternalDbClusterIpRange,
			},
		})
	}
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "workspace-isolation",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: EgressRules,
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPoliciesOpenPomerium(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyOpenPomerium(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyOpenPomerium(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "open-pomerium",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{
				MatchLabels: map[string]string{
					"app": "pomerium",
				},
			},
			Ingress: []networkingv1.NetworkPolicyIngressRule{
				{},
			},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Ingress"),
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyCodeServerToCoreApi(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyCodeServerToCoreApi(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyCodeServerToCoreApi(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "code-server-to-core-api",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{
				MatchLabels: map[string]string{
					"role": "code-server",
				},
			},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/namespace": "core",
								},
							},
							PodSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"app": "api",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyCodeServerToDbtApi(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyCodeServerToDbtApi(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyCodeServerToDbtApi(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-code-server-to-dbt-api",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{
				MatchLabels: map[string]string{
					"role": "code-server",
				},
			},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/namespace": "core",
								},
							},
							PodSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"app": "dbt-api",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyAirflowToCoreApi(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyAirflowToCoreApi(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyAirflowToCoreApi(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "airflow-to-core-api",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{
				MatchLabels: map[string]string{
					"tier": "airflow",
				},
			},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/namespace": "core",
								},
							},
							PodSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"app": "api",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyDbtDocsToCoreApi(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyDbtDocsToCoreApi(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyDbtDocsToCoreApi(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "dbt-docs-to-core-api",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{
				MatchLabels: map[string]string{
					"app": "dbt-docs",
				},
			},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/namespace": "core",
								},
							},
							PodSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"app": "api",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyAirflowToDbtApi(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyAirflowToDbtApi(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyAirflowToDbtApi(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-airflow-to-dbt-api",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{
				MatchLabels: map[string]string{
					// for more granularity: use the "component" label.
					"tier": "airflow",
				},
			},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/namespace": "core",
								},
							},
							PodSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"app": "dbt-api",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyAllowIngressController(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyAllowIngressController(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyAllowIngressController(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-ingress-controller",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"app.kubernetes.io/name": "ingress-nginx",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPoliciesAllowK8sApiServer(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyAllowK8sApiServer(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyAllowK8sApiServer(workspace *Workspace) *networkingv1.NetworkPolicy {
	var ips []networkingv1.NetworkPolicyPeer
	var ports []networkingv1.NetworkPolicyPort

	for _, ip := range workspace.Spec.ClusterApiServerIps.Ips {
		ips = append(ips, networkingv1.NetworkPolicyPeer{
			IPBlock: &networkingv1.IPBlock{
				CIDR: ip + "/32",
			},
		})
	}

	for _, port := range workspace.Spec.ClusterApiServerIps.Ports {
		ports = append(ports, networkingv1.NetworkPolicyPort{
			Protocol: ptrProtocol("TCP"),
			Port: &intstr.IntOrString{
				Type:   intstr.Type(0),
				IntVal: port,
			},
		})
	}

	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-k8s-apiserver",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To:    ips,
					Ports: ports,
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyAirflowLogsToLokiGateway(ctx context.Context, workspace *Workspace) error {
	networkPolicy := genNetworkPolicyAirflowLogsToLokiGateway(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func genNetworkPolicyAirflowLogsToLokiGateway(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-airflow-logs-to-loki-gateway",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{
				MatchLabels: map[string]string{
					// "k8s.datacoves.com/app": "airflow-promtail",
					"tier": "airflow",
				},
			},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/namespace": "prometheus",
								},
							},
							PodSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"app.kubernetes.io/component": "gateway",
									"app.kubernetes.io/instance":  "loki",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

// This is only for local environment
func (r *WorkspaceReconciler) networkPolicyAllowLocalPostgres(ctx context.Context, workspace *Workspace) error {
	networkPolicy := getNetworkPolicyAllowLocalPostgres(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

// This is only for local environment
func getNetworkPolicyAllowLocalPostgres(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-postgres",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/namespace": "core",
								},
							},
							PodSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"datacoves.com/adapter":  "core",
									"app.kubernetes.io/name": "postgresql",
								},
							},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

func (r *WorkspaceReconciler) networkPolicyAllowCrossEnvToSameProject(ctx context.Context, workspace *Workspace) error {
	networkPolicy := getNetworkPolicyAllowCrossEnvToSameProject(workspace)
	return reconcileNetworkPolicy(ctx, r.Client, r.Scheme, workspace, networkPolicy)
}

func getNetworkPolicyAllowCrossEnvToSameProject(workspace *Workspace) *networkingv1.NetworkPolicy {
	return &networkingv1.NetworkPolicy{
		TypeMeta: v1.TypeMeta{
			Kind:       "NetworkPolicy",
			APIVersion: "networking.k8s.io/v1",
		},
		ObjectMeta: v1.ObjectMeta{
			Name:      "allow-cross-environment-to-same-project",
			Namespace: workspace.GetNamespace(),
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: v1.LabelSelector{},
			Egress: []networkingv1.NetworkPolicyEgressRule{
				{
					To: []networkingv1.NetworkPolicyPeer{
						{
							NamespaceSelector: &v1.LabelSelector{
								MatchLabels: map[string]string{
									"k8s.datacoves.com/project": workspace.Spec.Project,
								},
							},
							PodSelector: &v1.LabelSelector{},
						},
					},
				},
			},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyType("Egress"),
			},
		},
	}
}

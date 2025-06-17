package controllers

import (
	"context"
	"os"
	"strconv"
	"strings"

	"sigs.k8s.io/controller-runtime/pkg/client"

	"k8s.io/apimachinery/pkg/api/errors"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"

	// apps "k8s.io/api/apps/v1"
	core "k8s.io/api/core/v1"
	networking "k8s.io/api/networking/v1"

	// rbac "k8s.io/api/rbac/v1"

	. "datacoves.com/operator/api/v1"
	u "datacoves.com/operator/controllers/utils"
)

// genServices generates all the workspace services.
func genServices(workspace *Workspace) []Service {
	workbenchPort := 80
	workbenchWebsockets := false
	if os.Getenv("LOCAL_WORKBENCH_IMAGE") != "" {
		workbenchPort = 3000
		workbenchWebsockets = true
	}

	services := []Service{
		{
			Kind:         "pomerium",
			Name:         "pomerium",
			DomainPrefix: "authenticate",
		},
		{
			Kind:                      "workbench",
			Name:                      "core-workbench-svc.core",
			DomainPrefix:              "",
			TargetPort:                intstr.FromInt(workbenchPort),
			Websockets:                workbenchWebsockets,
			AllowAnyAuthenticatedUser: true,
			Exists:                    true,
			ProxyInterceptErrors:      true,
		},
	}

	if workspace.ServiceEnabled("airbyte") {
		services = append(services, Service{
			Kind:                 "airbyte",
			Name:                 workspace.Name + "-airbyte-airbyte-webapp-svc",
			DomainPrefix:         "airbyte",
			Websockets:           true,
			Exists:               true,
			ProxyInterceptErrors: true,
		})
	}

	if workspace.ServiceEnabled("superset") {
		services = append(services, Service{
			Kind:                 "superset",
			Name:                 workspace.Name + "-superset",
			DomainPrefix:         "superset",
			TargetPort:           intstr.FromInt(8088),
			Port:                 8088,
			Exists:               true,
			ProxyInterceptErrors: true,
		})
	}

	if workspace.ServiceEnabled("airflow") {
		services = append(services, Service{
			Kind:                 "airflow",
			Name:                 workspace.Name + "-airflow-webserver",
			DomainPrefix:         "airflow",
			TargetPort:           intstr.FromInt(8080),
			Port:                 8080,
			Exists:               true,
			ProxyInterceptErrors: true,
		})
		services = append(services, Service{
			Kind:                             "airflow",
			Name:                             workspace.Name + "-airflow-webserver",
			DomainPrefix:                     "api-airflow",
			PathPrefix:                       "/api",
			TargetPort:                       intstr.FromInt(8080),
			Port:                             8080,
			Exists:                           true,
			AllowPublicUnauthenticatedAccess: true,
			ProxyInterceptErrors:             false,
		})
	}

	if workspace.ServiceEnabled("dbt-docs") {
		services = append(services, Service{
			Kind:                      "dbt-docs",
			Name:                      "dbt-docs",
			DomainPrefix:              "dbt-docs",
			AllowAnyAuthenticatedUser: true,
			ProxyInterceptErrors:      true,
		})
	}

	if workspace.ServiceEnabled("datahub") {
		services = append(services, Service{
			Kind:                 "datahub",
			Name:                 workspace.Name + "-datahub-datahub-frontend",
			DomainPrefix:         "datahub",
			TargetPort:           intstr.FromInt(9002),
			Port:                 9002,
			Exists:               true,
			ProxyInterceptErrors: true,
		})
	}

	for i, user := range workspace.Spec.Users {
		if workspace.ServiceEnabled("code-server") && user.HasPermissionForService("code-server") {
			services = append(services,
				Service{
					Kind:                 "code-server",
					Name:                 "code-server-" + user.Slug,
					DomainPrefix:         user.Slug + "-transform", // TODO: Rename to user.Slug + "-code",
					User:                 &workspace.Spec.Users[i],
					TargetPort:           intstr.FromInt(codeServerPort),
					Websockets:           true,
					ProxyInterceptErrors: false,
				},
				Service{
					Kind:                 "code-server", // Considered part of code-server.
					Name:                 "dbt-docs-" + user.Slug,
					Selector:             map[string]string{"app": "code-server-" + user.Slug},
					DomainPrefix:         user.Slug + "-dbt-docs",
					User:                 &workspace.Spec.Users[i],
					ProxyInterceptErrors: true,
				},
			)

			if user.IsLocalAirflowEnabled() {
				services = append(services,
					Service{
						Kind:                 "code-server", // Considered part of code-server.
						Name:                 "airflow-" + user.Slug,
						Selector:             map[string]string{"app": "code-server-" + user.Slug},
						DomainPrefix:         user.Slug + "-airflow",
						User:                 &workspace.Spec.Users[i],
						TargetPort:           intstr.FromInt(localAirflowPort),
						Port:                 localAirflowPort,
						PreserveHostHeader:   true,
						ProxyInterceptErrors: true,
					},
				)
			}

			if user.CodeServerAccess != "private" {
				sharedCodeServerService := Service{
					Kind:                 "code-server",
					Name:                 "shared-code-server-" + user.Slug,
					Selector:             map[string]string{"app": "code-server-" + user.Slug},
					DomainPrefix:         user.CodeServerShareCode,
					User:                 &workspace.Spec.Users[i],
					TargetPort:           intstr.FromInt(codeServerPort),
					Websockets:           true,
					ProxyInterceptErrors: false,
				}
				if user.CodeServerAccess == "authenticated" {
					sharedCodeServerService.AllowAnyAuthenticatedUser = true
				} else if user.CodeServerAccess == "public" {
					sharedCodeServerService.AllowPublicUnauthenticatedAccess = true
				}
				services = append(services,
					sharedCodeServerService,
				)
			}

			for exposureKey, exposureOptions := range user.CodeServerExposures {
				iport, err := strconv.Atoi(exposureOptions["port"])
				if err == nil {
					service := Service{
						Kind:                 "code-server",
						Selector:             map[string]string{"app": "code-server-" + user.Slug},
						Name:                 "code-server-" + exposureKey + "-" + user.Slug,
						DomainPrefix:         exposureOptions["share_code"],
						User:                 &workspace.Spec.Users[i],
						Port:                 int32(iport),
						TargetPort:           intstr.FromInt(iport),
						PreserveHostHeader:   true,
						ProxyInterceptErrors: true,
					}
					if user.CodeServerAccess == "authenticated" || exposureOptions["access"] == "authenticated" {
						service.AllowAnyAuthenticatedUser = true
					} else if user.CodeServerAccess == "public" || exposureOptions["access"] == "public" {
						service.AllowPublicUnauthenticatedAccess = true
					}
					if exposureOptions["websockets"] == "true" {
						service.Websockets = true
					}
					services = append(services,
						service,
					)
				}
			}
		}

	}

	for i, service := range services {
		prefix := ""
		if service.DomainPrefix != "" {
			prefix = service.DomainPrefix + "-"
		}
		services[i].Host = prefix + workspace.Name + "." + workspace.Spec.ClusterDomain
	}

	return services
}

func (r *WorkspaceReconciler) services(ctx context.Context, workspace *Workspace, services []Service) error {
	for _, service := range services {
		if service.Exists {
			continue
		}
		err := reconcileService(ctx, r.Client, r.Scheme, workspace, genService(workspace, &service))
		if err != nil {
			return err
		}
	}
	return nil
}

func genService(workspace *Workspace, service *Service) *core.Service {
	port := int32(80)
	if service.Port != 0 {
		port = service.Port
	}

	targetPort := intstr.FromInt(80)
	if service.TargetPort != intstr.FromInt(0) {
		targetPort = service.TargetPort
	}

	selector := service.Selector
	if selector == nil {
		selector = map[string]string{"app": service.Name}
	}

	return &core.Service{
		ObjectMeta: v1.ObjectMeta{
			Name:      service.Name,
			Namespace: workspace.Namespace,
		},
		Spec: core.ServiceSpec{
			Selector: selector,
			Ports: []core.ServicePort{
				{
					Protocol:   core.ProtocolTCP,
					Port:       port,
					TargetPort: targetPort,
				},
			},
		},
	}
}

// ingress reconciles the workspace's ingress rules.
func (r *WorkspaceReconciler) ingress(ctx context.Context, workspace *Workspace, services []Service) error {
	ingress := genIngress(workspace, services, false)
	ingressFound := networking.Ingress{}
	err := r.Get(ctx, client.ObjectKeyFromObject(ingress), &ingressFound)

	if err != nil && errors.IsNotFound(err) {
		err = r.Create(ctx, ingress)
	} else if err != nil {
		return err
	} else {
		err = r.Update(ctx, ingress)
	}

	if err != nil {
		return err
	}

	ingress = genIngress(workspace, services, true)
	ingressFound = networking.Ingress{}
	err = r.Get(ctx, client.ObjectKeyFromObject(ingress), &ingressFound)

	if err != nil && errors.IsNotFound(err) {
		return r.Create(ctx, ingress)
	} else if err != nil {
		return err
	} else {
		return r.Update(ctx, ingress)
	}
}

func genIngress(workspace *Workspace, services []Service, isIngressBackend bool) *networking.Ingress {
	rules := []networking.IngressRule{}
	tls := []networking.IngressTLS{}

	for _, service := range services {
		host := service.Host
		rule := networking.IngressRule{
			Host: host,
			IngressRuleValue: networking.IngressRuleValue{
				HTTP: &networking.HTTPIngressRuleValue{
					Paths: []networking.HTTPIngressPath{
						{
							Path:     "/",
							PathType: &u.PathTypePrefix,
							Backend: networking.IngressBackend{
								Service: &networking.IngressServiceBackend{
									Name: "pomerium",
									Port: networking.ServiceBackendPort{Number: 80},
								},
							},
						},
					},
				},
			},
		}

		if isIngressBackend && !service.ProxyInterceptErrors {
			rules = append(rules, rule)
		} else if !isIngressBackend && service.ProxyInterceptErrors {
			rules = append(rules, rule)
		}

		if workspace.Spec.CertManagerIssuer != "" {
			tls = append(tls, networking.IngressTLS{
				Hosts:      []string{host},
				SecretName: strings.ReplaceAll(host, ".", "-"),
			})
		}
	}

	annotations := map[string]string{
		"nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
		"nginx.ingress.kubernetes.io/ssl-redirect":       "true",
	}

	if !isIngressBackend {
		var errorPages = "error_page 404 500 502 503 504 \"https://cdn." + workspace.Spec.ClusterDomain + "/service/down/\";"
		annotations["nginx.ingress.kubernetes.io/server-snippet"] = "proxy_intercept_errors on; " + errorPages
	}

	if workspace.Spec.CertManagerIssuer != "" {
		annotations["cert-manager.io/cluster-issuer"] = workspace.Spec.CertManagerIssuer
	}

	dnsUrl := workspace.Spec.ExternalDnsUrl
	if dnsUrl != "" {
		annotations["external-dns.alpha.kubernetes.io/alias"] = "true"
		annotations["external-dns.alpha.kubernetes.io/target"] = dnsUrl
	}

	ingressName := "workspace-ingress"
	if isIngressBackend {
		ingressName = "workspace-ingress" + "-backend"
	}

	return &networking.Ingress{
		ObjectMeta: v1.ObjectMeta{
			Namespace:   workspace.Namespace,
			Name:        ingressName,
			Annotations: annotations,
		},
		Spec: networking.IngressSpec{
			Rules:            rules,
			TLS:              tls,
			IngressClassName: &u.StrNginx,
		},
	}
}

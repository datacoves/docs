package controllers

import (
	"context"
	"fmt"

	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"

	apps "k8s.io/api/apps/v1"
	autoscaling "k8s.io/api/autoscaling/v2"
	core "k8s.io/api/core/v1"

	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/yaml"

	. "datacoves.com/operator/api/v1"
	u "datacoves.com/operator/controllers/utils"
)

const (
	promeriumDeploymentName = "pomerium"
	pomeriumRedisName       = "pomerium-redis"
	pomeriumRedisPort       = 6379
)

type PomeriumPolicy struct {
	From string `json:"from"`
	To   string `json:"to"`

	AllowedUsers                     []string            `json:"allowed_users,omitempty"`
	AllowedIdpClaims                 map[string][]string `json:"allowed_idp_claims,omitempty"`
	AllowWebsockets                  bool                `json:"allow_websockets,omitempty"`
	SetResponseHeaders               map[string]string   `json:"set_response_headers,omitempty"`
	SetRequestHeaders                map[string]string   `json:"set_request_headers,omitempty"`
	Timeout                          string              `json:"timeout,omitempty"`
	AllowAnyAuthenticatedUser        bool                `json:"allow_any_authenticated_user,omitempty"`
	AllowPublicUnauthenticatedAccess bool                `json:"allow_public_unauthenticated_access,omitempty"`
	Prefix                           string              `json:"prefix,omitempty"`
	PreserveHostHeader               bool                `json:"host_rewrite_header,omitempty"`
}

// pomerium reconciles the namespace's resources required to run pomerium.
func (r *WorkspaceReconciler) pomerium(ctx context.Context, workspace *Workspace, services []Service) error {
	log := log.FromContext(ctx)

	base := map[string]interface{}{}
	baseSecret := core.Secret{}
	baseSecretKey := client.ObjectKey{
		Namespace: workspace.Namespace,
		Name:      workspace.Spec.Configs["pomerium-base-config"],
	}
	err := r.Get(ctx, baseSecretKey, &baseSecret)
	if err != nil {
		return err
	}
	err = yaml.Unmarshal(baseSecret.Data["config.yaml"], &base)
	if err != nil {
		return err
	}

	secret := genPomeriumConfigSecret(workspace, base, services)

	err = reconcileSecret(ctx, r.Client, r.Scheme, workspace, secret)
	if err != nil {
		return err
	}

	deploymentPomeriun := genPomeriumDeployment(workspace, secret.Name, services)
	err = reconcileDeployment(ctx, r.Client, r.Scheme, workspace, deploymentPomeriun)
	if err != nil {
		// Way to apply changes to immutable fields
		log.Error(err, "deployment could not be created or updated")
		log.Info("trying to recreate deployment:", "deplopyment", promeriumDeploymentName)
		err := deleteDeployment(ctx, r.Client, workspace.Namespace, promeriumDeploymentName)
		if err != nil {
			return err
		}
		err = reconcileDeployment(ctx, r.Client, r.Scheme, workspace, deploymentPomeriun)
		if err != nil {
			return err
		}
	}

	err = reconcileService(ctx, r.Client, r.Scheme, workspace, genPomeriumRedisService(workspace))
	if err != nil {
		return err
	}

	err = reconcileDeployment(ctx, r.Client, r.Scheme, workspace, genPomeriumRedisDeployment(workspace))
	if err != nil {
		return err
	}

	if workspace.HPA() {
		err = reconcileHPA(ctx, r.Client, r.Scheme, workspace, genPomeriumHPA(workspace, services))
		if err != nil {
			return err
		}
	}

	return nil
}

func genPomeriumDeployment(workspace *Workspace, configSecretName string, services []Service) *apps.Deployment {
	labels := map[string]string{
		"app":                   "pomerium",
		"datacoves.com/adapter": "pomerium",
	}

	meta := v1.ObjectMeta{
		Name:      promeriumDeploymentName,
		Namespace: workspace.Namespace,
		Labels:    labels,
	}

	authServiceUrl := "https://authenticate-" + workspace.Name + "." + workspace.Spec.ClusterDomain

	configVolumeName := "pomerium-config-volume"

	// Assuming that pomerium inits 4 services per second
	delay := len(services) / 4
	// incresing probes every 10 seconds, equivalent to 40 new services, or 20 new users
	livenessDelay := 30 + delay - (delay % 10)
	readinessDelay := 10 + delay - (delay % 10)

	pomeriumContainer := core.Container{
		Name:            "pomerium",
		Image:           workspace.ImageName("pomerium/pomerium"),
		ImagePullPolicy: core.PullIfNotPresent,
		Args:            []string{"-config", "/config/config.yaml"},
		Ports:           []core.ContainerPort{{ContainerPort: 80, Protocol: core.ProtocolTCP, Name: "http"}},
		VolumeMounts: []core.VolumeMount{
			{
				Name:      configVolumeName,
				MountPath: "/config",
				ReadOnly:  true,
			},
		},
		LivenessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/ping",
					Port: intstr.FromInt(80),
				},
			},
			// As the number of users grows, the pomerium config size grows and
			// pomerium takes longer to start. It is killed by the liveness probe
			// if it doesn't start fast enough.
			InitialDelaySeconds: int32(livenessDelay),
			PeriodSeconds:       30,
		},
		ReadinessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/ping",
					Port: intstr.FromInt(80),
				},
			},
			InitialDelaySeconds: int32(readinessDelay),
			PeriodSeconds:       30,
		},
		// https://deepsource.io/blog/zero-downtime-deployment/#towards-zero-downtime
		// The command doesn't matter, what we want is to delay the termination
		// of the pod for a little while so that it is alive while the ingress
		// reroutes traffic to new pods. Since the pomerium container only has
		// the pomerium binary, we run `pomerium -version` instead of `sleep x`.
		Lifecycle: &core.Lifecycle{
			PreStop: &core.LifecycleHandler{
				Exec: &core.ExecAction{
					Command: []string{"pomerium", "-version"},
				},
			},
		},
		Env: u.Env{}.
			Set("ADDRESS", ":80").
			Set("INSECURE_SERVER", "true").
			Set("AUTHENTICATE_SERVICE_URL", authServiceUrl).
			Set("AUTOCERT", "false"),
	}

	if resReqs, ok := workspace.Spec.ResourceRequirements["pomerium"]; ok {
		pomeriumContainer.Resources = resReqs
	}

	containers := []core.Container{
		pomeriumContainer,
	}

	volumes := []core.Volume{
		{
			Name: configVolumeName,
			VolumeSource: core.VolumeSource{
				Secret: &core.SecretVolumeSource{
					SecretName: configSecretName,
					Items: []core.KeyToPath{
						{Key: "config.yaml", Path: "config.yaml"},
					},
					DefaultMode: &u.Int32_0o644,
				},
			},
		},
	}

	// With maxUnavaliable = 0 and maxSurge > 1, existing pods aren't terminated
	// before new ones start.
	maxUnavailable := intstr.FromInt(0)
	maxSurge := intstr.FromInt(3)
	minReplicas := int32(1 + len(services)/120)
	if minReplicas > 5 {
		minReplicas = 5
	}

	deployment := &apps.Deployment{
		ObjectMeta: meta,
		Spec: apps.DeploymentSpec{
			Selector: &v1.LabelSelector{MatchLabels: labels},
			Replicas: &minReplicas,
			Template: core.PodTemplateSpec{
				ObjectMeta: meta,
				Spec: core.PodSpec{
					NodeSelector: u.GeneralNodeSelector,
					Containers:   containers,
					Volumes:      volumes,
					HostAliases: []core.HostAlias{
						{
							IP: workspace.Spec.InternalIp,
							Hostnames: []string{
								"api." + workspace.Spec.ClusterDomain,
							},
						},
					},
				},
			},
			MinReadySeconds: int32(1),
			Strategy: apps.DeploymentStrategy{
				Type: apps.RollingUpdateDeploymentStrategyType,
				RollingUpdate: &apps.RollingUpdateDeployment{
					MaxUnavailable: &maxUnavailable,
					MaxSurge:       &maxSurge,
				},
			},
		},
	}

	return deployment
}

func genPomeriumConfigSecret(workspace *Workspace, base map[string]interface{}, services []Service) *core.Secret {
	var pomeriumConfigLabels = map[string]string{"app": "pomerium", "datacoves.com/adapter": "pomerium"}

	// Copy the base config to config (shallow).
	config := make(map[string]interface{}, len(base))
	for k, v := range base {
		config[k] = v
	}

	policies := []PomeriumPolicy{}
	for _, service := range services {
		if service.Name == "pomerium" || !workspace.ServiceEnabled(service.Kind) {
			continue
		}
		to := "http://" + service.Name
		if service.Port != 0 {
			to += fmt.Sprintf(":%d", service.Port)
		}

		policy := PomeriumPolicy{
			From: "https://" + service.Host,
			To:   to,
			SetResponseHeaders: map[string]string{
				// This header allows the service to be embedded in an iframe
				// from the workbench domain.
				"Content-Security-Policy": "frame-ancestors 'self' " + workspace.WorkbenchDomain() + ";",
			},
			SetRequestHeaders: map[string]string{
				"X-Forwarded-Proto": "https",
			},
			AllowWebsockets:    service.Websockets,
			PreserveHostHeader: service.PreserveHostHeader,
		}

		if service.PathPrefix != "" {
			policy.Prefix = service.PathPrefix
		}

		if service.Kind == "airbyte" {
			policy.Timeout = "300s"
		}

		if service.AllowPublicUnauthenticatedAccess {
			// public access
			policy.AllowPublicUnauthenticatedAccess = true
		} else if service.AllowAnyAuthenticatedUser {
			// authenticated users
			policy.AllowAnyAuthenticatedUser = true
		} else {
			// specific authenticated users
			users := []string{}
			if service.User == nil {
				for _, user := range workspace.Spec.Users {
					for _, permission := range user.Permissions {
						if permission.Service == service.DomainPrefix && permission.Path == service.PathPrefix {
							users = append(users, user.Email)
						}
					}
				}
				policy.AllowedIdpClaims = map[string][]string{
					workspace.Spec.OidcUserId: users,
				}
			} else {
				policy.AllowedIdpClaims = map[string][]string{
					workspace.Spec.OidcUserId: {service.User.Email},
				}
			}
		}

		policies = append(policies, policy)
	}
	config["policy"] = policies

	data, err := yaml.Marshal(config)
	if err != nil {
		panic(err)
	}

	h := u.HashForName(data)

	return &core.Secret{
		ObjectMeta: v1.ObjectMeta{
			Name:      "pomerium-config-" + h,
			Namespace: workspace.Namespace,
			Labels:    pomeriumConfigLabels,
		},
		Type: core.SecretTypeOpaque,
		Data: map[string][]byte{"config.yaml": data},
	}
}

func genPomeriumRedisDeployment(workspace *Workspace) *apps.Deployment {
	labels := map[string]string{
		"app": pomeriumRedisName,
	}

	meta := v1.ObjectMeta{
		Name:      pomeriumRedisName,
		Namespace: workspace.Namespace,
		Labels:    labels,
	}

	usersVolumeName := "pomerium-redis-users"

	redisContainer := core.Container{
		Name:            "redis",
		Image:           workspace.ImageName("datacovesprivate/pomerium-redis"),
		ImagePullPolicy: core.PullIfNotPresent,
		Ports:           []core.ContainerPort{{ContainerPort: 6379, Protocol: core.ProtocolTCP}},
		VolumeMounts: []core.VolumeMount{
			{
				Name:      usersVolumeName,
				MountPath: "/etc/redis/users.acl",
				SubPath:   "users.acl",
				ReadOnly:  true,
			},
		},
	}

	if resReqs, ok := workspace.Spec.ResourceRequirements[pomeriumRedisName]; ok {
		redisContainer.Resources = resReqs
	}

	containers := []core.Container{
		redisContainer,
	}

	volumes := []core.Volume{
		{
			Name: usersVolumeName,
			VolumeSource: core.VolumeSource{
				Secret: &core.SecretVolumeSource{
					SecretName: workspace.Spec.Configs["pomerium-redis-users"],
					Items: []core.KeyToPath{
						{Key: "users.acl", Path: "users.acl"},
					},
					DefaultMode: &u.Int32_0o644,
				},
			},
		},
	}

	deployment := &apps.Deployment{
		ObjectMeta: meta,
		Spec: apps.DeploymentSpec{
			Selector: &v1.LabelSelector{MatchLabels: labels},
			Replicas: &u.Int32_1,
			Template: core.PodTemplateSpec{
				ObjectMeta: meta,
				Spec: core.PodSpec{
					NodeSelector: u.GeneralNodeSelector,
					Containers:   containers,
					Volumes:      volumes,
				},
			},
		},
	}

	return deployment
}

func genPomeriumRedisService(workspace *Workspace) *core.Service {
	return &core.Service{
		ObjectMeta: v1.ObjectMeta{
			Name:      pomeriumRedisName,
			Namespace: workspace.Namespace,
		},
		Spec: core.ServiceSpec{
			Selector: map[string]string{"app": pomeriumRedisName},
			Ports: []core.ServicePort{
				{
					Protocol:   core.ProtocolTCP,
					Port:       int32(pomeriumRedisPort),
					TargetPort: intstr.FromInt(pomeriumRedisPort),
				},
			},
		},
	}
}

func genPomeriumHPA(workspace *Workspace, services []Service) *autoscaling.HorizontalPodAutoscaler {
	minReplicas := int32(1 + len(services)/120)
	if minReplicas > 5 {
		minReplicas = 5
	}
	CPUUtilizationPercentage := int32(40)

	return &autoscaling.HorizontalPodAutoscaler{
		ObjectMeta: v1.ObjectMeta{
			Name:      "pomerium",
			Namespace: workspace.Namespace,
		},
		Spec: autoscaling.HorizontalPodAutoscalerSpec{
			ScaleTargetRef: autoscaling.CrossVersionObjectReference{
				Kind:       "Deployment",
				Name:       "pomerium",
				APIVersion: "apps/v1",
			},
			MinReplicas: &minReplicas,
			MaxReplicas: 10,
			Metrics: []autoscaling.MetricSpec{
				{
					Type: "Resource",
					Resource: &autoscaling.ResourceMetricSource{
						Name: "cpu",
						Target: autoscaling.MetricTarget{
							Type:               "Utilization",
							AverageUtilization: &CPUUtilizationPercentage,
						},
					},
				},
			},
		},
	}
}

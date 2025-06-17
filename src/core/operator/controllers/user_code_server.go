package controllers

import (
	"context"
	"strconv"
	"strings"

	"k8s.io/apimachinery/pkg/api/resource"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"

	apps "k8s.io/api/apps/v1"
	core "k8s.io/api/core/v1"
	rbac "k8s.io/api/rbac/v1"

	. "datacoves.com/operator/api/v1"
	u "datacoves.com/operator/controllers/utils"
)

const codeServerPort = 8443
const localAirflowPort = 8080

func (r *UserReconciler) codeServer(ctx context.Context, workspace *Workspace, user *User) error {
	if !workspace.ServiceEnabled("code-server") || !user.Spec.HasPermissionForService("code-server") {
		err := deleteDeployment(ctx, r.Client, workspace.Namespace, "code-server-"+user.Spec.Slug)
		return err
	}

	err := reconcileServiceAccount(ctx, r.Client, r.Scheme, workspace, genServiceAccount(workspace, &user.Spec))
	if err != nil {
		return err
	}

	err = reconcileRole(ctx, r.Client, r.Scheme, workspace, genRole(workspace, &user.Spec))
	if err != nil {
		return err
	}

	err = reconcileRoleBinding(ctx, r.Client, r.Scheme, workspace, genRoleBinding(workspace, &user.Spec))
	if err != nil {
		return err
	}

	err = reconcilePersistentVolumeClaim(ctx, r.Client, r.Scheme, user, genCodeServerPersistentVolumeClaim(workspace, &user.Spec))
	if err != nil {
		return err
	}
	return reconcileStatefulSet(ctx, r.Client, r.Scheme, user, genCodeServerStatefulSet(workspace, &user.Spec))
}

func codeServerName(user *UserSpec) string {
	return "code-server-" + user.Slug
}

func codeServerConfigVolumeName(user *UserSpec) string {
	return codeServerName(user) + "-config-volume"
}

func codeServerSecretsVolumeName(user *UserSpec) string {
	return codeServerName(user) + "-secrets-volume"
}

func genCodeServerStatefulSet(workspace *Workspace, user *UserSpec) *apps.StatefulSet {
	name := codeServerName(user)
	configVolume := codeServerConfigVolumeName(user)
	secretsVolume := codeServerSecretsVolumeName(user)

	labels := map[string]string{
		"app":  name,
		"role": "code-server",
	}

	meta := v1.ObjectMeta{
		Name:      name,
		Namespace: workspace.Namespace,
		Labels:    labels,
		Annotations: map[string]string{
			"kubectl.kubernetes.io/restartedAt":              user.CodeServerRestartedAt,
			"cluster-autoscaler.kubernetes.io/safe-to-evict": "false",
		},
	}

	codeServerPorts := []core.ContainerPort{
		{ContainerPort: codeServerPort, Protocol: core.ProtocolTCP, Name: "http"},
	}

	for exposureKey, exposureOptions := range user.CodeServerExposures {
		iport, err := strconv.Atoi(exposureOptions["port"])
		if err == nil {
			codeServerPorts = append(codeServerPorts, core.ContainerPort{ContainerPort: int32(iport), Protocol: core.ProtocolTCP, Name: exposureKey})
		}
	}

	codeServerContainer := core.Container{
		Name:            "code-server",
		Image:           workspace.ProfileImageName("datacovesprivate/code-server-code-server"),
		ImagePullPolicy: core.PullIfNotPresent,
		Ports:           codeServerPorts,
		LivenessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/",
					Port: intstr.IntOrString{
						Type:   intstr.Type(1),
						IntVal: 0,
						StrVal: "http",
					},
				},
			},
			InitialDelaySeconds: 120, // we needed to increment it since orrum takes > 1 min sometimes
			TimeoutSeconds:      1,
			PeriodSeconds:       10,
			SuccessThreshold:    1,
			FailureThreshold:    3,
		},
		ReadinessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/",
					Port: intstr.IntOrString{
						Type:   intstr.Type(1),
						IntVal: 0,
						StrVal: "http",
					},
				},
			},
			InitialDelaySeconds: 15,
			TimeoutSeconds:      1,
			PeriodSeconds:       5,
			SuccessThreshold:    1,
			FailureThreshold:    3,
		},
		EnvFrom: []core.EnvFromSource{
			{SecretRef: &core.SecretEnvSource{
				LocalObjectReference: core.LocalObjectReference{
					Name: user.SecretName,
				},
			}},
		},

		VolumeMounts: []core.VolumeMount{
			{
				Name:      configVolume,
				MountPath: "/config",
			},
			{
				Name:      secretsVolume,
				MountPath: "/opt/datacoves/user",
				ReadOnly:  true,
			},
		},
		// TODO: Deprecate DBT_HOME and CODE_HOME
		Env: u.Env{}.
			Set("PUID", "1000").
			Set("PGID", "1000").
			Set("TZ", "America/Los_Angeles").
			Set("DBT_HOME", "/config/workspace/"+workspace.Spec.DbtHome).
			Set("DATACOVES__DBT_HOME", "/config/workspace/"+workspace.Spec.DbtHome).
			Set("DATACOVES__USER_EMAIL", user.Email).
			Set("DATACOVES__USER_FULLNAME", user.Name).
			Set("DATACOVES__REPOSITORY_URL", workspace.Spec.SshGitRepo).
			Set("DATACOVES__REPOSITORY_CLONE", workspace.Spec.CloneRepository).
			Set("DATACOVES__USER_SLUG", user.Slug),
	}

	dbtDocsContainer := core.Container{
		Name:            "dbt-docs",
		Image:           workspace.ImageName("datacovesprivate/observe-local-dbt-docs"),
		ImagePullPolicy: core.PullIfNotPresent,
		Ports:           []core.ContainerPort{{ContainerPort: 80, Protocol: core.ProtocolTCP}},
		Env: u.Env{}.
			Set("DBT_HOME", "workspace/"+workspace.Spec.DbtHome).
			Set("DATACOVES__DBT_HOME", "/config/workspace/"+workspace.Spec.DbtHome),
		VolumeMounts: []core.VolumeMount{
			{
				Name:      configVolume,
				MountPath: "/usr/share/nginx/html/code-server",
				ReadOnly:  true,
			},
		},
	}

	// Use dbt-osmosis image if dbt-core-interface was not found
	img := workspace.ProfileImageName("datacovesprivate/code-server-dbt-core-interface")
	if strings.HasSuffix(img, ":latest") {
		img = workspace.ProfileImageName("datacovesprivate/code-server-dbt-osmosis")
	}

	dbtSyncServerContainer := core.Container{
		Name:            "dbt-core-interface",
		Image:           img,
		ImagePullPolicy: core.PullIfNotPresent,
		Ports:           []core.ContainerPort{{ContainerPort: 8581, Protocol: core.ProtocolTCP}},
		EnvFrom: []core.EnvFromSource{
			{SecretRef: &core.SecretEnvSource{
				LocalObjectReference: core.LocalObjectReference{
					Name: user.SecretName,
				},
			}},
		},
		Env: u.Env{}.
			Set("DBT_HOME", "workspace/"+workspace.Spec.DbtHome).
			Set("DATACOVES__DBT_HOME", "/config/workspace/"+workspace.Spec.DbtHome).
			Set("CODE_HOME", "/config").
			Set("DATACOVES__CODE_HOME", "/config").
			Set("DATACOVES__USER_EMAIL", user.Email).
			Set("DATACOVES__USER_FULLNAME", user.Name).
			Set("DATACOVES__REPOSITORY_URL", workspace.Spec.SshGitRepo).
			Set("DATACOVES__REPOSITORY_CLONE", workspace.Spec.CloneRepository).
			Set("DATACOVES__USER_SLUG", user.Slug),
		VolumeMounts: []core.VolumeMount{
			{
				Name:      configVolume,
				MountPath: "/config",
			},
		},
	}

	localAirflowEnv := u.Env{}.
		Set("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", "sqlite:////opt/airflow/database/airflow.db").
		Set("AIRFLOW__WEBSERVER__ENABLE_PROXY_FIX", "True")

	// Copy over environment variables
	for _, nameval := range user.LocalAirflowEnvironment {
		localAirflowEnv = localAirflowEnv.Set(nameval.Name, nameval.Value)
	}

	// Make a local airflow container if we're doing such things.
	localAirflowContainer := core.Container{
		Name:            "local-airflow",
		Image:           workspace.ProfileImageName("datacovesprivate/airflow-airflow"),
		ImagePullPolicy: core.PullIfNotPresent,
		Ports:           []core.ContainerPort{{ContainerPort: 8080, Protocol: core.ProtocolTCP}},
		EnvFrom: []core.EnvFromSource{
			{SecretRef: &core.SecretEnvSource{
				LocalObjectReference: core.LocalObjectReference{
					Name: user.SecretName,
				},
			}},
		},
		LivenessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/",
					Port: intstr.FromInt(8080),
				},
			},
			InitialDelaySeconds: 60,
			TimeoutSeconds:      30,
			PeriodSeconds:       5,
			SuccessThreshold:    1,
			FailureThreshold:    20,
		},
		ReadinessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/health",
					Port: intstr.FromInt(8080),
				},
			},
			InitialDelaySeconds: 15,
			TimeoutSeconds:      30,
			PeriodSeconds:       5,
			SuccessThreshold:    1,
			FailureThreshold:    20,
		},
		Env: localAirflowEnv,

		VolumeMounts: []core.VolumeMount{
			{
				Name:      configVolume,
				MountPath: "/opt/airflow/dags/repo",
				SubPath:   "workspace",
			},
			{
				Name:      configVolume,
				MountPath: "/opt/airflow/database",
				SubPath:   "local-airflow/db",
			},
			{
				Name:      configVolume,
				MountPath: "/opt/airflow/logs",
				SubPath:   "local-airflow/logs",
			},
			{
				Name:      secretsVolume,
				MountPath: "/opt/datacoves/user",
				ReadOnly:  true,
			},
		},
		Command: []string{
			"/bin/bash",
		},
		Args: []string{
			"-c",
			"cp /opt/datacoves/user/webserver_config.py /opt/airflow && " +
				"/entrypoint standalone",
		},
	}

	if workspace.DontUseWsgi() {
		dbtSyncServerContainer.Args = []string{
			"--no-uwsgi",
		}
	}

	if resReqs, ok := workspace.Spec.ResourceRequirements["code-server"]; ok {
		codeServerContainer.Resources = resReqs
	}
	if resReqs, ok := workspace.Spec.ResourceRequirements["code-server-dbt-docs"]; ok {
		dbtDocsContainer.Resources = resReqs
	}
	if resReqs, ok := workspace.Spec.ResourceRequirements["code-server-dbt-core-interface"]; ok {
		dbtSyncServerContainer.Resources = resReqs
	}
	if resReqs, ok := workspace.Spec.ResourceRequirements["code-server-local-airflow"]; ok {
		localAirflowContainer.Resources = resReqs
	}

	containers := []core.Container{codeServerContainer}

	if workspace.LocalDbtDocs() {
		containers = append(containers, dbtDocsContainer)
	}

	if workspace.DbtSync() {
		containers = append(containers, dbtSyncServerContainer)
	}

	/*
	 * Note that the order of volumes matters -- the if statement
	 * immediately after this depends on the secrets being the second
	 * item in the volume array.
	 */
	volumes := []core.Volume{
		{
			Name: configVolume,
			VolumeSource: core.VolumeSource{
				PersistentVolumeClaim: &core.PersistentVolumeClaimVolumeSource{
					ClaimName: configVolume,
				},
			},
		},
		{
			Name: secretsVolume,
			VolumeSource: core.VolumeSource{
				Secret: &core.SecretVolumeSource{
					SecretName: user.SecretName,
					Items: []core.KeyToPath{
						{
							Key:  "DATACOVES__SSL_KEYS_JSON",
							Path: "ssl_keys.json",
						},
						{
							Key:  "DATACOVES__SSH_KEYS_JSON",
							Path: "ssh_keys.json",
						},
						{
							Key:  "DATACOVES__PROFILE_FILES",
							Path: "files.json",
						},
					},
				},
			},
		},
	}

	/*
	 * We only get passed this key if local airflow is enabled
	 * on the django side.
	 *
	 * This relies on volumes[1] being the secrets.
	 */
	if user.IsLocalAirflowEnabled() {
		containers = append(containers, localAirflowContainer)
		volumes[1].VolumeSource.Secret.Items =
			append(
				volumes[1].VolumeSource.Secret.Items,
				core.KeyToPath{
					Key:  "DATACOVES__AIRFLOW_WEBSERVER_CONFIG",
					Path: "webserver_config.py",
				},
			)
	}

	replicas := int32(1)
	if !user.CodeServerEnabled() {
		replicas = int32(0)
	}

	// Diabling service links prevents Kubernetes from injecting a bunch
	// of extra environment variables we don't want.
	enableServiceLinks := bool(false)

	podSpec := core.PodSpec{
		NodeSelector:       u.VolumedNodeSelector,
		ServiceAccountName: "code-server-" + user.Slug + "-sa",
		Containers:         containers,
		Volumes:            volumes,
		HostAliases: []core.HostAlias{
			{
				IP:        workspace.Spec.InternalIp,
				Hostnames: []string{"api." + workspace.Spec.ClusterDomain},
			},
		},
		// This prevents the extra environment variables from appearing
		EnableServiceLinks: &enableServiceLinks,
	}

	workspace.AddDnsToPodSpecIfNeeded(&podSpec)

	statefulSet := &apps.StatefulSet{
		ObjectMeta: meta,
		Spec: apps.StatefulSetSpec{
			Selector: &v1.LabelSelector{MatchLabels: labels},
			Replicas: &replicas,
			Template: core.PodTemplateSpec{
				ObjectMeta: meta,
				Spec:       podSpec,
			},
			// Migrate Deploynent to StatefulSets?
			// https://stackoverflow.com/questions/52848176/re-attach-volume-claim-on-deployment-update
			// Strategy: apps.DeploymentStrategy{
			//	Type: "Recreate",
			//},
		},
	}

	return statefulSet
}

func genCodeServerPersistentVolumeClaim(workspace *Workspace, user *UserSpec) *core.PersistentVolumeClaim {
	return &core.PersistentVolumeClaim{
		ObjectMeta: v1.ObjectMeta{
			Namespace: workspace.Namespace,
			Name:      codeServerConfigVolumeName(user),
		},
		Spec: core.PersistentVolumeClaimSpec{
			AccessModes: []core.PersistentVolumeAccessMode{core.ReadWriteOnce},
			Resources: core.ResourceRequirements{
				Requests: core.ResourceList{
					core.ResourceStorage: resource.MustParse("20Gi"),
				},
			},
		},
	}
}

func genServiceAccount(workspace *Workspace, user *UserSpec) *core.ServiceAccount {
	return &core.ServiceAccount{
		ObjectMeta: v1.ObjectMeta{
			Namespace: workspace.Namespace,
			Name:      "code-server-" + user.Slug + "-sa",
		},
		ImagePullSecrets: []core.LocalObjectReference{
			{
				Name: workspace.Spec.ImagePullSecret,
			},
		},
	}
}

func genRole(workspace *Workspace, user *UserSpec) *rbac.Role {
	return &rbac.Role{
		ObjectMeta: v1.ObjectMeta{
			Namespace: workspace.Namespace,
			Name:      codeServerName(user) + "-pod-exec-role",
		},
		Rules: []rbac.PolicyRule{
			{
				APIGroups:     []string{""},
				Resources:     []string{"pods", "pods/exec"},
				ResourceNames: []string{codeServerName(user) + "-0"}, // Suffix for statefulSet
				Verbs:         []string{"create", "get", "list"},
			},
		},
	}
}

func genRoleBinding(workspace *Workspace, user *UserSpec) *rbac.RoleBinding {
	return &rbac.RoleBinding{
		ObjectMeta: v1.ObjectMeta{
			Namespace: workspace.Namespace,
			Name:      codeServerName(user) + "-pod-exec-rolebinding",
		},
		RoleRef: rbac.RoleRef{
			APIGroup: "rbac.authorization.k8s.io",
			Kind:     "Role",
			Name:     codeServerName(user) + "-pod-exec-role",
		},
		Subjects: []rbac.Subject{
			{
				Kind:      "ServiceAccount",
				Name:      codeServerName(user) + "-sa",
				Namespace: workspace.Namespace,
			},
		},
	}
}

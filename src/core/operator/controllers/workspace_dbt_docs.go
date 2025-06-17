package controllers

import (
	"context"
	"strings"

	"k8s.io/apimachinery/pkg/api/resource"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
	"sigs.k8s.io/controller-runtime/pkg/log"

	apps "k8s.io/api/apps/v1"
	core "k8s.io/api/core/v1"

	. "datacoves.com/operator/api/v1"
	u "datacoves.com/operator/controllers/utils"
)

func (r *WorkspaceReconciler) dbtDocs(ctx context.Context, workspace *Workspace) error {
	log := log.FromContext(ctx)

	if !workspace.ServiceEnabled("dbt-docs") {
		err := deleteDeployment(ctx, r.Client, workspace.Namespace, "dbt-docs")
		return err
	}

	secretsName := workspace.Spec.Configs["dbt-docs-git-sync-secrets"]

	deployment := genDbtDocsDeployment(workspace, secretsName)
	err := reconcileDeployment(ctx, r.Client, r.Scheme, workspace, deployment)
	if err != nil {
		// Way to apply changes to immutable fields
		log.Error(err, "deployment could not be created or updated")
		log.Info("trying to recreate deployment:", "deplopyment", "dbt-docs")
		err := deleteDeployment(ctx, r.Client, workspace.Namespace, "dbt-docs")
		if err != nil {
			return err
		}
		err = reconcileDeployment(ctx, r.Client, r.Scheme, workspace, deployment)
		if err != nil {
			return err
		}

		return err
	}

	return err
}

func genDbtDocsDeployment(workspace *Workspace, gitSyncSecretsName string) *apps.Deployment {
	name := "dbt-docs"

	labels := map[string]string{
		"app":                   name,
		"datacoves.com/adapter": name,
	}

	htmlVolumeName := "dbt-docs-volume"

	meta := v1.ObjectMeta{
		Name:      name,
		Namespace: workspace.Namespace,
		Labels:    labels,
	}

	gitRepo := workspace.Spec.SshGitRepo
	gitSyncSsh := "true"

	if workspace.Spec.GitCloneStrategy != "ssh_clone" {
		gitRepo = workspace.Spec.HttpGitRepo
		gitSyncSsh = "false"
	}

	gitRepoParts := strings.Split(gitRepo, "/")
	gitRepoPath := gitRepoParts[len(gitRepoParts)-1]

	dbtDocsContainer := core.Container{
		Name:            "dbt-docs",
		Image:           workspace.ImageName("datacovesprivate/observe-dbt-docs"),
		ImagePullPolicy: core.PullIfNotPresent,
		Ports:           []core.ContainerPort{{ContainerPort: 80, Protocol: core.ProtocolTCP, Name: "http"}},
		LivenessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/healthz",
					Port: intstr.IntOrString{
						Type:   intstr.Type(1),
						IntVal: 0,
						StrVal: "http",
					},
				},
			},
			InitialDelaySeconds: 60,
			TimeoutSeconds:      1,
			PeriodSeconds:       10,
			SuccessThreshold:    1,
			FailureThreshold:    3,
		},
		ReadinessProbe: &core.Probe{
			ProbeHandler: core.ProbeHandler{
				HTTPGet: &core.HTTPGetAction{
					Path: "/healthz",
					Port: intstr.IntOrString{
						Type:   intstr.Type(1),
						IntVal: 0,
						StrVal: "http",
					},
				},
			},
			InitialDelaySeconds: 5,
			TimeoutSeconds:      1,
			PeriodSeconds:       5,
			SuccessThreshold:    1,
			FailureThreshold:    3,
		},
		Env: u.Env{}.
			Set("DBT_DOCS_GIT_PATH", gitRepoPath),
		VolumeMounts: []core.VolumeMount{
			{
				Name:      htmlVolumeName,
				MountPath: "/usr/share/nginx/html/repo",
				ReadOnly:  true,
			},
		},
	}

	gitSyncImage := workspace.ImageName("registry.k8s.io/git-sync/git-sync")
	gitSyncImageParts := strings.Split(gitSyncImage, ":")
	gitSyncImageTag := gitSyncImageParts[len(gitSyncImageParts)-1]
	gitSyncRoot := "/git"

	// To avoid duplicates of "refs/heads/" in the branch name
	gitBranch := "refs/heads/" + strings.Replace(workspace.Spec.DbtDocsGitBranch, "refs/heads/", "", 1)
	env := u.Env{}

	if strings.HasPrefix(gitSyncImageTag, "v3") {
		// git-sync v3
		env = env.
			Set("GIT_SYNC_REPO", gitRepo).
			Set("GIT_SYNC_SSH", gitSyncSsh).
			Set("GIT_SYNC_BRANCH", gitBranch).
			Set("GIT_KNOWN_HOSTS", "false").
			Set("GIT_SYNC_DEPTH", "1").
			Set("GIT_PATH_CLONE", "300").
			Set("GIT_SYNC_ROOT", gitSyncRoot).
			Set("GIT_SYNC_MAX_SYNC_FAILURES", "5")

		if len(workspace.Spec.DbtDocsAskpassUrl) > 0 {
			env = env.
				Set("GIT_SYNC_ASKPASS_URL", workspace.Spec.DbtDocsAskpassUrl)
		}
	} else {
		// git-sync v4
		env = env.
			Set("GITSYNC_REPO", gitRepo).
			Set("GIT_SYNC_SSH", gitSyncSsh).
			Set("GITSYNC_REF", gitBranch).
			Set("GITSYNC_SSH_KNOWN_HOSTS", "false").
			Set("GITSYNC_DEPTH", "1").
			Set("GITSYNC_SYNC_TIMEOUT", "300s").
			Set("GITSYNC_ROOT", gitSyncRoot).
			Set("GITSYNC_MAX_FAILURES", "5")

		if len(workspace.Spec.DbtDocsAskpassUrl) > 0 {
			env = env.
				Set("GITSYNC_ASKPASS_URL", workspace.Spec.DbtDocsAskpassUrl)
		}
	}

	volumeMounts := []core.VolumeMount{
		{
			Name:      htmlVolumeName,
			MountPath: gitSyncRoot,
		},
	}

	htmlVolumeLimit := resource.MustParse("12Gi")
	volumes := []core.Volume{
		{
			Name: htmlVolumeName,
			VolumeSource: core.VolumeSource{
				EmptyDir: &core.EmptyDirVolumeSource{
					SizeLimit: &htmlVolumeLimit,
				},
			},
		},
	}

	if gitSyncSsh == "false" {
		if len(workspace.Spec.DbtDocsAskpassUrl) == 0 {
			if strings.HasPrefix(gitSyncImageTag, "v3") {
				// git-sync v3
				env = env.AddFromSecret(gitSyncSecretsName,
					"GIT_SYNC_USERNAME",
					"GIT_SYNC_PASSWORD",
				)
			} else {
				// git-sync v4
				env = env.AddFromSecret(gitSyncSecretsName,
					"GITSYNC_USERNAME",
					"GITSYNC_PASSWORD",
				)
			}
		}
	} else {
		sshKeyVolumeName := "ssh-key-volume"
		volumeMounts = append(volumeMounts, core.VolumeMount{
			Name:      sshKeyVolumeName,
			MountPath: "/etc/git-secret",
		})
		volumes = append(volumes, core.Volume{
			Name: sshKeyVolumeName,
			VolumeSource: core.VolumeSource{
				Secret: &core.SecretVolumeSource{
					SecretName: gitSyncSecretsName,
					Items: []core.KeyToPath{
						{Key: "gitSshKey", Path: "ssh"},
					},
					DefaultMode: &u.Int32_0o644,
				},
			},
		})
	}

	gitSyncContainer := core.Container{
		Name:            "git-sync",
		Image:           gitSyncImage,
		ImagePullPolicy: core.PullIfNotPresent,
		Env:             env,
		VolumeMounts:    volumeMounts,
	}

	if resReqs, ok := workspace.Spec.ResourceRequirements["dbt-docs"]; ok {
		dbtDocsContainer.Resources = resReqs
		gitSyncContainer.Resources = resReqs
	}

	containers := []core.Container{
		dbtDocsContainer,
		gitSyncContainer,
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
					// TODO: Review running pod as root, if we switch to SSH.
					// https://github.com/kubernetes/git-sync/blob/release-3.x/docs/ssh.md
					// SecurityContext: &core.PodSecurityContext{
					// 	RunAsUser: &u.Int64_0,
					// },
				},
			},
		},
	}

	return deployment
}

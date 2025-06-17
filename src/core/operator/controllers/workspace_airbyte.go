package controllers

import (
	"context"

	"sigs.k8s.io/controller-runtime/pkg/client"
	ctrlu "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"

	core "k8s.io/api/core/v1"
	rbac "k8s.io/api/rbac/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	. "datacoves.com/operator/api/v1"
)

func (r *WorkspaceReconciler) airbyte(ctx context.Context, workspace *Workspace) error {
	log := log.FromContext(ctx)

	ns := workspace.Namespace
	releaseName := workspace.Name + "-airbyte"
	gotRelease := HelmRelease{}
	err := r.Get(ctx, client.ObjectKey{Namespace: ns, Name: releaseName}, &gotRelease)
	if err != nil && !errors.IsNotFound(err) {
		return err
	}
	releaseNotFound := errors.IsNotFound(err)

	// airbyte admin service account
	err = reconcileServiceAccount(ctx, r.Client, r.Scheme, workspace, GenSchedulerServiceAccount(workspace))
	if err != nil {
		return err
	}
	err = reconcileRole(ctx, r.Client, r.Scheme, workspace, GenSchedulerRole(workspace))
	if err != nil {
		return err
	}
	err = reconcileRoleBinding(ctx, r.Client, r.Scheme, workspace, GenSchedulerRoleBinding(workspace))
	if err != nil {
		return err
	}

	if !workspace.ServiceEnabled("airbyte") {
		if releaseNotFound {
			return nil
		}
		log.Info("delete HelmRelease", "name", releaseName)
		return r.Delete(ctx, &gotRelease)
	}

	release := &HelmRelease{
		ObjectMeta: v1.ObjectMeta{
			Namespace: ns,
			Name:      releaseName,
		},
		Spec: HelmReleaseSpec{
			RepoURL:    workspace.Spec.Charts["airbyte"]["repo"],
			RepoName:   workspace.Spec.Charts["airbyte"]["repo_name"],
			Chart:      workspace.Spec.Charts["airbyte"]["chart"],
			Version:    workspace.Spec.Charts["airbyte"]["version"],
			ValuesName: workspace.Spec.Configs["airbyte-values"],
		},
	}

	// If the release is already in the state we want it, do nothing.
	if gotRelease.Spec.ValuesName == release.Spec.ValuesName {
		return nil
	}

	// Set the owner of the deployment, so that it is deleted when the owner is deleted.
	err = ctrlu.SetControllerReference(workspace, release, r.Scheme)
	if err != nil {
		return err
	}
	if releaseNotFound {
		log.Info("create HelmRelease", "name", releaseName)
		return r.Create(ctx, release)
	} else {
		log.Info("update HelmRelease", "name", releaseName)
		release.ResourceVersion = gotRelease.ResourceVersion
		return r.Update(ctx, release)
	}
}

func GenSchedulerServiceAccount(workspace *Workspace) *core.ServiceAccount {
	return &core.ServiceAccount{
		ObjectMeta: v1.ObjectMeta{
			Namespace: workspace.Namespace,
			Name:      "airbyte-admin",
		},
		ImagePullSecrets: []core.LocalObjectReference{
			{
				Name: workspace.Spec.ImagePullSecret,
			},
		},
	}
}

func GenSchedulerRole(workspace *Workspace) *rbac.Role {
	return &rbac.Role{
		ObjectMeta: v1.ObjectMeta{
			Namespace: workspace.Namespace,
			Name:      "airbyte-admin-role",
		},
		Rules: []rbac.PolicyRule{
			{
				APIGroups: []string{"*"},
				Resources: []string{"jobs", "pods", "pods/log", "pods/exec", "pods/attach", "secrets", "configmaps"},
				Verbs:     []string{"get", "list", "watch", "create", "update", "patch", "delete"},
			},
		},
	}
}

func GenSchedulerRoleBinding(workspace *Workspace) *rbac.RoleBinding {
	return &rbac.RoleBinding{
		ObjectMeta: v1.ObjectMeta{
			Namespace: workspace.Namespace,
			Name:      "airbyte-admin-binding",
		},
		RoleRef: rbac.RoleRef{
			APIGroup: "rbac.authorization.k8s.io",
			Kind:     "Role",
			Name:     "airbyte-admin-role",
		},
		Subjects: []rbac.Subject{
			{
				Kind: "ServiceAccount",
				Name: "airbyte-admin",
			},
		},
	}
}

package controllers

import (
	"context"

	"sigs.k8s.io/controller-runtime/pkg/client"
	ctrlu "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"

	"k8s.io/apimachinery/pkg/api/errors"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	. "datacoves.com/operator/api/v1"
)

func (r *WorkspaceReconciler) airflow(ctx context.Context, workspace *Workspace) error {
	log := log.FromContext(ctx)
	ns := workspace.Namespace
	releaseName := workspace.Name + "-airflow"
	gotRelease := HelmRelease{}
	err := r.Get(ctx, client.ObjectKey{Namespace: ns, Name: releaseName}, &gotRelease)
	if err != nil && !errors.IsNotFound(err) {
		return err
	}
	releaseNotFound := errors.IsNotFound(err)

	if !workspace.ServiceEnabled("airflow") {
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
			RepoURL:    workspace.Spec.Charts["airflow"]["repo"],
			RepoName:   workspace.Spec.Charts["airflow"]["repo_name"],
			Chart:      workspace.Spec.Charts["airflow"]["chart"],
			Version:    workspace.Spec.Charts["airflow"]["version"],
			ValuesName: workspace.Spec.Configs["airflow-values"],
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

func (r *WorkspaceReconciler) airflowPromtail(ctx context.Context, workspace *Workspace) error {
	log := log.FromContext(ctx)
	ns := workspace.Namespace
	releaseName := workspace.Name + "-airflow-promtail"
	gotRelease := HelmRelease{}
	err := r.Get(ctx, client.ObjectKey{Namespace: ns, Name: releaseName}, &gotRelease)
	if err != nil && !errors.IsNotFound(err) {
		return err
	}
	releaseNotFound := errors.IsNotFound(err)

	if !workspace.ServiceEnabled("airflow") || !workspace.ServiceEnabled("AirflowLogs") {
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
			RepoURL:    workspace.Spec.Charts["promtail"]["repo"],
			RepoName:   workspace.Spec.Charts["promtail"]["repo_name"],
			Chart:      workspace.Spec.Charts["promtail"]["chart"],
			Version:    workspace.Spec.Charts["promtail"]["version"],
			ValuesName: workspace.Spec.Configs["airflow-promtail-values"],
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

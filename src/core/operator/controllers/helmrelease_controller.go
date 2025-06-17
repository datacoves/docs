package controllers

import (
	"context"

	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	ctrlu "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"

	. "datacoves.com/operator/api/v1"
	"datacoves.com/operator/helm"
)

const (
	helmReleaseFinalizer = "datacoves.com/helmrelease-finalizer"
)

// HelmReleaseReconciler reconciles a HelmRelease object
type HelmReleaseReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// SetupWithManager sets up the controller with the Manager.
func (r *HelmReleaseReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&HelmRelease{}, builder.WithPredicates(predicate.GenerationChangedPredicate{})).
		WithOptions(controller.Options{MaxConcurrentReconciles: 6}).
		Complete(r)
}

//+kubebuilder:rbac:groups=datacoves.com,resources=helmreleases,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=datacoves.com,resources=helmreleases/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=datacoves.com,resources=helmreleases/finalizers,verbs=update

func (r *HelmReleaseReconciler) Reconcile(ctx context.Context, req ctrl.Request) (res ctrl.Result, err error) {
	got := HelmRelease{}
	release := &got
	err = r.Get(ctx, req.NamespacedName, release)
	if err != nil {
		if errors.IsNotFound(err) {
			// The release no longer exists. There is nothing to do and nothing has
			// failed so we must return without an error (or we would be retried).
			err = nil
		}
		return
	}

	// Add the release name to every log call from this reconcile.
	logger := log.FromContext(ctx).WithName(release.Name)
	ctx = log.IntoContext(ctx, logger)
	log := log.FromContext(ctx)
	log.Info("reconciling", "generation", release.Generation)
	defer func() {
		if err == nil {
			log.Info("reconciled", "generation", release.Generation)
		}
	}()

	// Uninstall on HelmResource deletion using a finalizer.
	if release.ObjectMeta.DeletionTimestamp.IsZero() {
		if !ctrlu.ContainsFinalizer(release, helmReleaseFinalizer) {
			ctrlu.AddFinalizer(release, helmReleaseFinalizer)
			err = r.Update(ctx, release)
			if err != nil {
				return
			}
		}
	} else {
		if ctrlu.ContainsFinalizer(release, helmReleaseFinalizer) {
			helm.Uninstall(releaseChart(release))
			ctrlu.RemoveFinalizer(release, helmReleaseFinalizer)
			err = r.Update(ctx, release)
			if err != nil {
				return
			}
		}

		err = nil
		return
	}

	helm.Install(
		releaseChart(release),
		helm.InstallArgs{
			RepoURL:    release.Spec.RepoURL,
			RepoName:   release.Spec.RepoName,
			Version:    release.Spec.Version,
			ValuesName: release.Spec.ValuesName,
		})

	err = nil
	return
}

func releaseChart(release *HelmRelease) helm.Chart {
	return helm.Chart{
		Namespace: release.Namespace,
		Name:      release.Spec.Chart,
		Release:   release.Name,
	}
}

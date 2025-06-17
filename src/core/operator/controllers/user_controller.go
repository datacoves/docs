package controllers

import (
	"context"

	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"

	// apps "k8s.io/api/apps/v1"
	// core "k8s.io/api/core/v1"
	// rbac "k8s.io/api/rbac/v1"

	. "datacoves.com/operator/api/v1"
)

// UserReconciler reconciles a User object
type UserReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// SetupWithManager sets up the controller with the Manager.
func (r *UserReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&User{}, builder.WithPredicates(predicate.GenerationChangedPredicate{})).
		WithOptions(controller.Options{MaxConcurrentReconciles: 12}).
		Complete(r)
}

//+kubebuilder:rbac:groups=datacoves.com,resources=users,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=datacoves.com,resources=users/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=datacoves.com,resources=users/finalizers,verbs=update

func (r *UserReconciler) Reconcile(ctx context.Context, req ctrl.Request) (res ctrl.Result, err error) {
	got := User{}
	user := &got
	err = r.Get(ctx, req.NamespacedName, user)
	if err != nil {
		if errors.IsNotFound(err) {
			// The user no longer exists. There is nothing to do and nothing has
			// failed so we must return without an error (or we would be retried).
			err = nil
		}
		return
	}
	if !user.DeletionTimestamp.IsZero() {
		// Do nothing if the user is being deleted.
		return
	}

	// Add the user name to every log call from this reconcile.
	logger := log.FromContext(ctx).WithName(user.Name)
	ctx = log.IntoContext(ctx, logger)
	log := log.FromContext(ctx)
	log.Info("reconciling", "generation", user.Generation)
	defer func() {
		if err == nil {
			log.Info("reconciled", "generation", user.Generation)
		}
	}()

	workspaceName := ""
	for _, ref := range user.GetOwnerReferences() {
		if ref.Kind == "Workspace" {
			workspaceName = ref.Name
			break
		}
	}

	if workspaceName == "" {
		err = nil // NOTE: err is nil for now, so we won't retry.
		log.Error(err, "user without owner", "user name", user.Name)
		return
	}

	gotw := Workspace{}
	workspace := &gotw
	err = r.Get(ctx, client.ObjectKey{Namespace: user.Namespace, Name: workspaceName}, workspace)
	if err != nil {
		if errors.IsNotFound(err) {
			// The workspace no longer exists. There is nothing to do and nothing has
			// failed so we must return without an error (or we would be retried).
			err = nil
		}
		return
	}

	err = r.codeServer(ctx, workspace, user)
	if err != nil {
		log.Error(err, "error in stage: code-server")
		return
	}

	err = nil
	return
}

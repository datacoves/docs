package controllers

import (
	"context"

	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"

	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"

	. "datacoves.com/operator/api/v1"
)

// AccountReconciler reconciles a Account object
type AccountReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// SetupWithManager sets up the controller with the Manager.
func (r *AccountReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&Account{}, builder.WithPredicates(predicate.GenerationChangedPredicate{})).
		Watches(
			&source.Kind{Type: &Workspace{}},
			handler.EnqueueRequestsFromMapFunc(r.enqueueForWatched),
			builder.WithPredicates(predicate.ResourceVersionChangedPredicate{}),
		).
		// As long as we have 1 workspace this parameter improves nothing, so
		// let's not risk it for now.
		// WithOptions(controller.Options{MaxConcurrentReconciles: 12}).
		Complete(r)
}

// When a watched obj changes, trigger a reconcile if the obj has a workspace annotation.
func (r *AccountReconciler) enqueueForWatched(obj client.Object) []reconcile.Request {
	kind := obj.GetObjectKind().GroupVersionKind()
	if kind.Group == GroupVersion.Group && kind.Version == GroupVersion.Version && kind.Kind == "Workspace" {
		workspaceNs := obj.GetNamespace()
		workspaceName := obj.GetName()
		workspace := Workspace{}
		err := r.Get(context.TODO(), client.ObjectKey{Namespace: workspaceNs, Name: workspaceName}, &workspace)
		if err != nil {
			// If we can't get a workspace with that name, don't reconcile.
			return []reconcile.Request{}
		}

		accountName := workspace.Spec.Account
		accountNs := "dca-" + accountName
		account := Account{}
		err = r.Get(context.TODO(), client.ObjectKey{Namespace: accountNs, Name: accountName}, &account)
		if err != nil {
			// If we can't get an account with that name, don't reconcile.
			return []reconcile.Request{}
		}

		return []reconcile.Request{
			{
				NamespacedName: types.NamespacedName{
					Name:      account.Name,
					Namespace: account.Namespace,
				},
			},
		}
	}
	return []reconcile.Request{}
}

//+kubebuilder:rbac:groups=datacoves.com,resources=accounts,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=datacoves.com,resources=accounts/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=datacoves.com,resources=accounts/finalizers,verbs=update

func (r *AccountReconciler) Reconcile(ctx context.Context, req ctrl.Request) (res ctrl.Result, err error) {
	got := Account{}
	account := &got
	err = r.Get(ctx, req.NamespacedName, account)
	if err != nil {
		if errors.IsNotFound(err) {
			// The account no longer exists. There is nothing to do and nothing has
			// failed so we must return without an error (or we would be retried).
			err = nil
		}
		return
	}
	if !account.DeletionTimestamp.IsZero() {
		// Do nothing if the account is being deleted.
		return
	}

	// Add the account name to every log call from this reconcile.
	logger := log.FromContext(ctx).WithName(account.Name)
	ctx = log.IntoContext(ctx, logger)
	log := log.FromContext(ctx)
	log.Info("reconciling", "generation", account.Generation)
	defer func() {
		if err == nil {
			log.Info("reconciled", "generation", account.Generation)
		}
	}()

	err = addImagePullSecretToDefaultServiceAccount(ctx, r.Client, account.Namespace, account.Spec.ImagePullSecret)
	if err != nil {
		log.Error(err, "error in stage: imagePullSecret")
		return
	}

	return ctrl.Result{}, nil
}

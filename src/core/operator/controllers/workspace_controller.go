package controllers

import (
	"context"
	"fmt"

	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/builder"
	"sigs.k8s.io/controller-runtime/pkg/client"
	ctrlu "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/handler"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/predicate"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"sigs.k8s.io/controller-runtime/pkg/source"

	"k8s.io/apimachinery/pkg/api/errors"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"

	// apps "k8s.io/api/apps/v1"
	core "k8s.io/api/core/v1"

	// rbac "k8s.io/api/rbac/v1"

	. "datacoves.com/operator/api/v1"
)

// WorkspaceReconciler reconciles a Workspace object
type WorkspaceReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

// Service describes a service within the workspace (e.g. airbyte, code-server).
// Ingress rules and pomerium configuration is derived from these records.
type Service struct {
	Kind         string    // The kind of service. Values are the same as workspace.Services keys.
	Name         string    // Name of the kubernetes service resource.
	Host         string    // Host/domain where the service is externally accessible.
	DomainPrefix string    // Prefix used in the domain.
	PathPrefix   string    // https://www.pomerium.com/reference/#prefix
	User         *UserSpec // Who this service is for, or nil if the resource is namespace wide.

	Selector                         map[string]string // If not set, {"app": service.Name} is used.
	Port                             int32
	TargetPort                       intstr.IntOrString
	Exists                           bool // If existing, it means it won't create the service
	Websockets                       bool
	AllowAnyAuthenticatedUser        bool
	AllowPublicUnauthenticatedAccess bool
	PreserveHostHeader               bool
	ProxyInterceptErrors             bool
}

// SetupWithManager sets up the controller with the Manager.
func (r *WorkspaceReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&Workspace{}, builder.WithPredicates(predicate.GenerationChangedPredicate{})).
		Owns(&User{}).
		Owns(&HelmRelease{}).
		// NOTE: We could watch the owned resources we create too
		// (e.g. Deployments) and that way the operator would try to reset any
		// modifications to them. The problem is that our own updates to those
		// resources also trigger reconciliation, and it can be hard to program
		// in a way that doesn't go into an infinite update-reconcile loop.
		// Reconciliation already has to be idempotent. To watch owned+created
		// resources we would also have to make it achieve a fixed point.
		// So we don't do that. We assume we are the only ones touching the
		// resources we create, and we are not triggered by changes to them.
		// NOTE: Watching the secrets and configmaps we depend on means that
		// when multiple resources are modified at once (by workspace.py), then
		// multiple reconciliations are triggered. This works OK. It could be
		// better to watch only the Workspace resource and have it reference
		// immutable secrets and configmaps so that django can create all the
		// new secrets and update the Workspace once, triggering a single reconcile.
		Watches(
			&source.Kind{Type: &core.Secret{}},
			handler.EnqueueRequestsFromMapFunc(r.enqueueForWatched),
			builder.WithPredicates(predicate.ResourceVersionChangedPredicate{}),
		).
		Watches(
			&source.Kind{Type: &core.ConfigMap{}},
			handler.EnqueueRequestsFromMapFunc(r.enqueueForWatched),
			builder.WithPredicates(predicate.ResourceVersionChangedPredicate{}),
		).
		// As long as we have 1 workspace this parameter improves nothing, so
		// let's not risk it for now.
		// WithOptions(controller.Options{MaxConcurrentReconciles: 12}).
		Complete(r)
}

// When a watched obj changes, trigger a reconcile if the obj has a workspace annotation.
func (r *WorkspaceReconciler) enqueueForWatched(obj client.Object) []reconcile.Request {
	ns := obj.GetNamespace()
	annots := obj.GetAnnotations()
	if workspaceName, found := annots["datacoves.com/workspace"]; found && workspaceName != "" {
		workspace := Workspace{}
		err := r.Get(context.TODO(), client.ObjectKey{Namespace: ns, Name: workspaceName}, &workspace)
		if err != nil {
			// If we can't get a workspace with that name, don't reconcile.
			return []reconcile.Request{}
		}

		return []reconcile.Request{
			{
				NamespacedName: types.NamespacedName{
					Name:      workspace.Name,
					Namespace: workspace.Namespace,
				},
			},
		}
	}
	return []reconcile.Request{}
}

//+kubebuilder:rbac:groups=datacoves.com,resources=workspaces,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=datacoves.com,resources=workspaces/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=datacoves.com,resources=workspaces/finalizers,verbs=update

//+kubebuilder:rbac:groups=datacoves.com,resources=users,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=datacoves.com,resources=users/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=datacoves.com,resources=users/finalizers,verbs=update

//+kubebuilder:rbac:groups=apps,resources=deployments;daemonsets;replicasets;statefulsets,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=networking.k8s.io,resources=ingresses;networkpolicies,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=rbac.authorization.k8s.io,resources=roles;rolebindings;clusterroles;clusterrolebindings,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups="",resources=pods;services;persistentvolumeclaims;configmaps;secrets;serviceaccounts;namespaces;events,verbs=get;list;watch;create;update;patch;delete

// For airbyte-admin service account...
//+kubebuilder:rbac:groups=*,resources=cronjobs;jobs;pods;pods/attach;pods/exec;pods/log,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=autoscaling,resources=horizontalpodautoscalers,verbs=create;delete;get;list;patch;update;watch
//+kubebuilder:rbac:groups=policy,resources=poddisruptionbudgets,verbs=create;delete;get;list;patch;update;watch

func (r *WorkspaceReconciler) Reconcile(ctx context.Context, req ctrl.Request) (res ctrl.Result, err error) {
	ns := core.Namespace{}
	err = r.Get(ctx, client.ObjectKey{Name: req.Namespace}, &ns)
	if err != nil {
		if errors.IsNotFound(err) {
			err = nil
		}
		return
	}
	if !ns.DeletionTimestamp.IsZero() {
		// Do nothing if the namespace is being deleted.
		return
	}

	got := Workspace{}
	workspace := &got
	err = r.Get(ctx, req.NamespacedName, workspace)
	if err != nil {
		if errors.IsNotFound(err) {
			// The workspace no longer exists. There is nothing to do and nothing has
			// failed so we must return without an error (or we would be retried).
			err = nil
		}
		return
	}
	if !workspace.DeletionTimestamp.IsZero() {
		// Do nothing if the workspace is being deleted.
		return
	}

	// Add the workspace name to every log call from this reconcile.
	logger := log.FromContext(ctx).WithName(workspace.Name)
	ctx = log.IntoContext(ctx, logger)
	log := log.FromContext(ctx)
	log.Info("reconciling", "generation", workspace.Generation)
	defer func() {
		if err == nil {
			log.Info("reconciled", "generation", workspace.Generation)
		}
	}()

	services := genServices(workspace)

	r.networkPolicies(ctx, workspace)

	err = r.services(ctx, workspace, services)
	if err != nil {
		log.Error(err, "error in stage: services")
		return
	}

	err = r.ingress(ctx, workspace, services)
	if err != nil {
		log.Error(err, "error in stage: ingress")
		return
	}

	err = addImagePullSecretToDefaultServiceAccount(ctx, r.Client, workspace.Namespace, workspace.Spec.ImagePullSecret)
	if err != nil {
		log.Error(err, "error in stage: imagePullSecret")
		return
	}

	err = r.pomerium(ctx, workspace, services)
	if err != nil {
		log.Error(err, "error in stage: pomerium")
		return
	}

	err = r.users(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: users")
		return
	}

	err = r.superset(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: superset")
		return
	}

	err = r.minio(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: minio")
		return
	}

	err = r.elastic(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: elastic")
		return
	}

	err = r.neo4j(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: neo4j")
		return
	}

	err = r.postgresql(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: postgresql")
		return
	}

	err = r.kafka(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: kafka")
		return
	}

	err = r.datahub(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: datahub")
		return
	}

	err = r.airbyte(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: airbyte")
		return
	}

	err = r.dbtDocs(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: dbt docs")
		return
	}

	err = r.airflow(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: airflow")
		return
	}

	err = r.airflowPromtail(ctx, workspace)
	if err != nil {
		log.Error(err, "error in stage: airlfowPromtail")
		return
	}

	err = nil
	return
}

func (r *WorkspaceReconciler) users(ctx context.Context, workspace *Workspace) error {
	// Get existing users and put them into the users map.
	userList := UserList{}
	err := r.List(ctx, &userList, &client.ListOptions{Namespace: workspace.Namespace})
	if err != nil && !errors.IsNotFound(err) {
		return fmt.Errorf("users list: %w", err)
	}
	users := map[string]User{}
	for _, user := range userList.Items {
		users[user.Name] = user
	}

	// Create or update users comparing existing users with the workspace spec.
	for _, spec := range workspace.Spec.Users {
		user, exists := users[spec.Slug]
		if !exists || !user.Spec.Equals(spec) {
			err = r.user(ctx, workspace, spec)
			if err != nil {
				return fmt.Errorf("user (%s): %w", user.Name, err)
			}
		}
		// Remove the user from the users map so that when this for loop endsthe
		// ones that remain are those not in the workspace spec.
		delete(users, spec.Slug)
	}

	log := log.FromContext(ctx)

	// Delete users not in the spec.
	// TODO: Sort users before iterating to avoid infinite reconcile retries.
	// Random range iteration order + controller runtime retries = trouble.
	for _, user := range users {
		log.Info("delete User", "name", user.Name)
		err = r.Delete(ctx, &user)
		if err != nil && !errors.IsNotFound(err) {
			return fmt.Errorf("user delete: %w", err)
		}
	}

	return nil
}

func (r *WorkspaceReconciler) user(ctx context.Context, workspace *Workspace, spec UserSpec) error {
	name := spec.Slug

	user := &User{
		ObjectMeta: v1.ObjectMeta{Namespace: workspace.GetNamespace(), Name: name},
		Spec:       spec,
	}

	// Set the owner of the deployment, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(workspace, user, r.Scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := User{}
	err = r.Get(ctx, client.ObjectKeyFromObject(user), &got)
	if err != nil && !errors.IsNotFound(err) {
		return err
	}
	if errors.IsNotFound(err) {
		log.Info("create User", "name", name)
		return r.Create(ctx, user)
	}
	user.ResourceVersion = got.ResourceVersion
	log.Info("update User", "name", name)
	return r.Update(ctx, user)
}

// imagePullSecret sets the image pull secret of the workspace on the namespace's
// default service account, so all pods in the namespace can use it to pull
// images.
func addImagePullSecretToDefaultServiceAccount(ctx context.Context, c client.Client, namespace, secretName string) error {
	if secretName == "" {
		// TODO: Review. Might change imagePullSecret to be required and return
		// an error here.
		return nil
	}

	sa := core.ServiceAccount{}
	err := c.Get(ctx, client.ObjectKey{Name: "default", Namespace: namespace}, &sa)
	if err != nil {
		return err
	}

	found := false
	for _, ips := range sa.ImagePullSecrets {
		if ips.Name == secretName {
			found = true
			break
		}
	}

	if !found {
		// TODO: https://aws.github.io/aws-eks-best-practices/security/docs/iam/#disable-auto-mounting-of-service-account-tokens
		// sa.AutomountServiceAccountToken = &u.False
		sa.ImagePullSecrets = append(sa.ImagePullSecrets, core.LocalObjectReference{
			Name: secretName,
		})
		return c.Update(ctx, &sa)
	}

	return nil
}

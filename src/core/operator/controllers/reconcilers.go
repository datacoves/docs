package controllers

import (
	"context"
	"fmt"

	"github.com/go-logr/logr"

	"sigs.k8s.io/controller-runtime/pkg/client"
	ctrlu "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/log"

	"k8s.io/apimachinery/pkg/api/equality"
	"k8s.io/apimachinery/pkg/api/errors"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"

	apps "k8s.io/api/apps/v1"
	autoscaling "k8s.io/api/autoscaling/v2"
	core "k8s.io/api/core/v1"
	networking "k8s.io/api/networking/v1"
	policy "k8s.io/api/policy/v1beta1"
	rbac "k8s.io/api/rbac/v1"
)

// Helpers to reconcile resources. Used controllerutils.CreateOrUpdate for
// reference, but these are saner because they take in the desired state of the
// object instead of a mutate function to bang it into shape.

func logCreate(log logr.Logger, kind, name string) {
	log.Info("create "+kind, "name", name)
}

func logUpdate(log logr.Logger, kind, name, reason string) {
	log.Info("update "+kind, "name", name, "reason", reason)
}

func logDelete(log logr.Logger, kind, name string) {
	log.Info("delete "+kind, "name", name)
}

func reconcileDeployment(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *apps.Deployment) error {
	// Set the owner of the deployment, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := apps.Deployment{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "Deployment", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		reason := reasonToUpdateDeployment(log, &got.Spec, &obj.Spec)
		if reason != "" {
			logUpdate(log, "Deployment", obj.Name, reason)
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reconcileStatefulSet(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *apps.StatefulSet) error {
	// Set the owner of the statefulset, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := apps.StatefulSet{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "Statefulset", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		reason := reasonToUpdateStatefulSet(log, &got.Spec, &obj.Spec)
		if reason != "" {
			logUpdate(log, "Statefulset", obj.Name, reason)
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reconcileNetworkPolicy(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *networking.NetworkPolicy) error {
	// Set the owner of the network policy, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := networking.NetworkPolicy{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "NetworkPolicy", obj.Name)
		return c.Create(ctx, obj)
	}
	return c.Update(ctx, obj)
}

func reconcileHPA(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *autoscaling.HorizontalPodAutoscaler) error {
	// Set the owner of the HPA, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := autoscaling.HorizontalPodAutoscaler{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "HorizontalPodAutoscaler", obj.Name)
		return c.Create(ctx, obj)
	}
	return c.Update(ctx, obj)
}

// NOTE: If this function is returning a reason to update when nothing has
// really changed, it is most likely because the objects are different in a
// trivial way, often because obj has zero values for some field (relying on the
// API setting some defaults) and what we got has the field set.
// So, the equality comparison we want depends on what the libraries do.
// No good answer with this approach... We'll have to keep refining our
// equality comparisons until it behaves like we need it to.
// Another stopgap measure is to set defaults explicitly when creating objects.
func reasonToUpdateDeployment(log logr.Logger, got, obj *apps.DeploymentSpec) string {
	// These are just forks of golang's reflect.DeepEqual with special handling
	// for a few k8s api types like resource.Quantity. The only semantic thing
	// about them is the name... Better than nothing, I guess...
	eq := equality.Semantic.DeepEqual
	eqd := equality.Semantic.DeepDerivative

	switch {
	case !eq(got.Replicas, obj.Replicas):
		return "replicas"
	case !eqd(got.Selector, obj.Selector):
		return "selector"
	}

	return reasonToUpdatePodTemplate(log, &got.Template.Spec, &obj.Template.Spec)
}

func reasonToUpdateStatefulSet(log logr.Logger, got, obj *apps.StatefulSetSpec) string {
	// These are just forks of golang's reflect.DeepEqual with special handling
	// for a few k8s api types like resource.Quantity. The only semantic thing
	// about them is the name... Better than nothing, I guess...
	eq := equality.Semantic.DeepEqual
	eqd := equality.Semantic.DeepDerivative

	switch {
	case !eq(got.Replicas, obj.Replicas):
		return "replicas"
	case !eqd(got.Selector, obj.Selector):
		return "selector"
	}

	return reasonToUpdatePodTemplate(log, &got.Template.Spec, &obj.Template.Spec)
}

func reasonToUpdatePodTemplate(log logr.Logger, got, obj *core.PodSpec) string {
	eq := equality.Semantic.DeepEqual
	eqd := equality.Semantic.DeepDerivative

	switch {
	case !eq(got.NodeSelector, obj.NodeSelector):
		return "template.spec.nodeSelector"
	case !eqd(got.Volumes, obj.Volumes):
		return "template.spec.volumes"
	}

	if len(obj.Containers) != len(got.Containers) {
		return "template.spec.containers"
	}

	for i, objc := range obj.Containers {
		gotc := got.Containers[i]

		// If the spec containers order is mantained, this won't be needed, but
		// just in case, we check if the names match, and if they don't we look
		// for a container with a matching name. If we haven't found one, the
		// specs differ and the deployment should be updated.
		if gotc.Name != objc.Name {
			found := false
			for _, c := range obj.Containers {
				if gotc.Name == objc.Name {
					found = true
					gotc = c
					break
				}
			}
			if !found {
				return "container.name"
			}
		}

		switch {
		case gotc.Name != objc.Name:
			return "container.name"
		case gotc.Image != objc.Image:
			return "container.image"
		case gotc.ImagePullPolicy != objc.ImagePullPolicy:
			return "container.imagePullPolicy"
		case gotc.WorkingDir != objc.WorkingDir:
			return "container.workingDir"
		case gotc.Stdin != objc.Stdin:
			return "container.stdin"
		case gotc.TTY != objc.TTY:
			return "container.tty"

		case !eq(gotc.Env, objc.Env):
			return "container.env"
		case !eqd(gotc.EnvFrom, objc.EnvFrom):
			return "container.envFrom"
		case !eqd(gotc.Ports, objc.Ports):
			return "containter.ports"
		case !eqd(gotc.VolumeMounts, objc.VolumeMounts):
			return "container.volumeMounts"
		case !eq(gotc.Resources, objc.Resources):
			return "container.resources"
		// We monitor liveness/readiness probes changes only on initialdelayseconds property since it's changed
		// dynamically on pomerium. We SHOULD NOT monitor other properties of liveness/readiness probes
		// since we don't set explicit values to all of them and k8s sets defaults (changes them)
		case gotc.LivenessProbe != nil && objc.LivenessProbe != nil && gotc.LivenessProbe.InitialDelaySeconds != objc.LivenessProbe.InitialDelaySeconds:
			return "container.LivenessProbe.InitialDelaySeconds"
		case gotc.ReadinessProbe != nil && objc.ReadinessProbe != nil && gotc.ReadinessProbe.InitialDelaySeconds != objc.ReadinessProbe.InitialDelaySeconds:
			return "container.ReadinessProbe.InitialDelaySeconds"
		}
	}

	return ""
}

func reconcileDaemonSet(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *apps.DaemonSet) error {
	// Set the owner of the deployment, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := apps.DaemonSet{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "DaemonSet", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		reason := reasonToUpdateDaemonSet(log, &got.Spec, &obj.Spec)
		if reason != "" {
			logUpdate(log, "DaemonSet", obj.Name, reason)
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reasonToUpdateDaemonSet(log logr.Logger, got, obj *apps.DaemonSetSpec) string {
	// These are just forks of golang's reflect.DeepEqual with special handling
	// for a few k8s api types like resource.Quantity. The only semantic thing
	// about them is the name... Better than nothing, I guess...
	// eq := equality.Semantic.DeepEqual
	eqd := equality.Semantic.DeepDerivative

	switch {
	case !eqd(got.Selector, obj.Selector):
		return "selector"
	}

	return reasonToUpdatePodTemplate(log, &got.Template.Spec, &obj.Template.Spec)
}

func reconcileSecret(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *core.Secret) error {
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := core.Secret{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "Secret", obj.Name)
		return c.Create(ctx, obj)
	}

	// NOTE: No updates. We treat Secrets as immutable.

	return err
}

func reconcileConfigMap(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *core.ConfigMap) error {
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := core.ConfigMap{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "ConfigMap", obj.Name)
		return c.Create(ctx, obj)
	}

	// NOTE: No updates. We treat ConfigMaps as immutable.

	return err
}

func reconcileService(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *core.Service) error {
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := core.Service{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "Service", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		reason := reasonToUpdateService(log, &got.Spec, &obj.Spec)
		if reason != "" {
			// Updates are tricky. Instead we delete the service and return an
			// error so reconciliation runs again and recreates it.
			err := c.Delete(ctx, &got)
			if err != nil {
				return err
			}
			return fmt.Errorf("Service %s spec mismatch. Deleting and recreating", obj.Name)
		}
	}
	return err
}

func reasonToUpdateService(log logr.Logger, got, obj *core.ServiceSpec) string {
	eqd := equality.Semantic.DeepDerivative

	switch {
	case !eqd(got.Ports, obj.Ports):
		if len(got.Ports) == len(obj.Ports) {
			// Set equal the fields that we want to ignore and compare again.
			for i, port := range obj.Ports {
				got.Ports[i].NodePort = port.NodePort
			}
			if eqd(got.Ports, obj.Ports) {
				return ""
			}
		}
		return "ports"
	case !eqd(got.Selector, obj.Selector):
		return "selector"
	}
	return ""
}

func reconcilePersistentVolumeClaim(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *core.PersistentVolumeClaim) error {
	// Let's not set the owner ref for now, in case we want the PVCs to outlive
	// the workspace.
	// err := ctrlu.SetControllerReference(owner, obj, scheme)
	// if err != nil {
	// 	return err
	// }

	log := log.FromContext(ctx)

	got := core.PersistentVolumeClaim{}
	err := c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "PersistentVolumeClaim", obj.Name)
		return c.Create(ctx, obj)
	}

	return err
}

func reconcileServiceAccount(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *core.ServiceAccount) error {
	// Set the owner of the ServiceAccount, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := core.ServiceAccount{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "ServiceAccount", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		eq := equality.Semantic.DeepEqual
		reason := ""
		if !eq(got.ImagePullSecrets, obj.ImagePullSecrets) {
			reason = "imagePullSecrets"
		}
		if !eq(got.AutomountServiceAccountToken, obj.AutomountServiceAccountToken) {
			reason += " automountServiceAccountToken"
		}
		if reason != "" {
			logUpdate(log, "ServiceAccount", obj.Name, reason)
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reconcileRole(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *rbac.Role) error {
	// Set the owner of the Role, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := rbac.Role{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "Role", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		if !rulesEqual(got.Rules, obj.Rules) {
			logUpdate(log, "Role", obj.Name, "rules")
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reconcileRoleBinding(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *rbac.RoleBinding) error {
	// Set the owner of the RoleBinding, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := rbac.RoleBinding{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "RoleBinding", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		eqd := equality.Semantic.DeepDerivative
		reason := ""
		if !eqd(got.RoleRef, obj.RoleRef) {
			reason = "roleRef"
		}
		if !eqd(got.Subjects, obj.Subjects) {
			reason += " subjects"
		}
		if reason != "" {
			logUpdate(log, "RoleBinding", obj.Name, reason)
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reconcileClusterRole(ctx context.Context, c client.Client, scheme *runtime.Scheme, obj *rbac.ClusterRole) error {
	log := log.FromContext(ctx)

	got := rbac.ClusterRole{}
	err := c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "ClusterRole", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		eqd := equality.Semantic.DeepDerivative
		if !eqd(got.Rules, obj.Rules) {
			logUpdate(log, "ClusterRole", obj.Name, "rules")
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reconcileClusterRoleBinding(ctx context.Context, c client.Client, scheme *runtime.Scheme, obj *rbac.ClusterRoleBinding) error {
	log := log.FromContext(ctx)

	got := rbac.ClusterRoleBinding{}
	err := c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "ClusterRoleBinding", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		eqd := equality.Semantic.DeepDerivative
		reason := ""
		if !eqd(got.RoleRef, obj.RoleRef) {
			reason = "roleRef"
		}
		if !eqd(got.Subjects, obj.Subjects) {
			reason += " subjects"
		}
		if reason != "" {
			logUpdate(log, "ClusterRoleBinding", obj.Name, reason)
			return c.Update(ctx, obj)
		}
	}
	return err
}

func reconcilePodDisruptionPolicy(ctx context.Context, c client.Client, scheme *runtime.Scheme, owner v1.Object, obj *policy.PodDisruptionBudget) error {
	// Set the owner of the PodDisruptionBudget, so that it is deleted when the owner is deleted.
	err := ctrlu.SetControllerReference(owner, obj, scheme)
	if err != nil {
		return err
	}

	log := log.FromContext(ctx)

	got := policy.PodDisruptionBudget{}
	err = c.Get(ctx, client.ObjectKeyFromObject(obj), &got)
	if err != nil && errors.IsNotFound(err) {
		logCreate(log, "PodDisruptionBudget", obj.Name)
		return c.Create(ctx, obj)
	}
	if err == nil {
		eq := equality.Semantic.DeepEqual
		reason := ""
		if !eq(got.Spec.Selector, obj.Spec.Selector) {
			reason = "selector"
		}
		if !eq(got.Spec.MinAvailable, obj.Spec.MinAvailable) {
			reason += " minAvailable"
		}
		if reason != "" {
			logUpdate(log, "PodDisruptionBudget", obj.Name, reason)
			return c.Update(ctx, obj)
		}
	}
	return err
}

func deleteDeployments(ctx context.Context, c client.Client, namespace string, names ...string) error {
	for _, name := range names {
		err := deleteDeployment(ctx, c, namespace, name)
		if err != nil {
			return err
		}
	}
	return nil
}

func deleteDeployment(ctx context.Context, c client.Client, namespace string, name string) error {
	got := apps.Deployment{}
	err := c.Get(ctx, client.ObjectKey{Namespace: namespace, Name: name}, &got)
	if err != nil && errors.IsNotFound(err) {
		return nil
	}
	if err == nil {
		log := log.FromContext(ctx)
		logDelete(log, "Deployment", name)
		return c.Delete(ctx, &got)
	}
	return err
}

func deleteServices(ctx context.Context, c client.Client, namespace string, names ...string) error {
	for _, name := range names {
		err := deleteService(ctx, c, namespace, name)
		if err != nil {
			return err
		}
	}
	return nil
}

func deleteService(ctx context.Context, c client.Client, namespace string, name string) error {
	got := core.Service{}
	err := c.Get(ctx, client.ObjectKey{Namespace: namespace, Name: name}, &got)
	if err != nil && errors.IsNotFound(err) {
		return nil
	}
	if err == nil {
		log := log.FromContext(ctx)
		logDelete(log, "Service", name)
		return c.Delete(ctx, &got)
	}
	return err
}

func rulesEqual(got []rbac.PolicyRule, obj []rbac.PolicyRule) bool {
	if len(got) != len(obj) {
		return false
	}

	for i := range got {
		if !equality.Semantic.DeepDerivative(got[i].Resources, obj[i].Resources) ||
			!equality.Semantic.DeepDerivative(got[i].Verbs, obj[i].Verbs) ||
			!equality.Semantic.DeepDerivative(got[i].APIGroups, obj[i].APIGroups) {
			return false
		}
	}

	return true
}

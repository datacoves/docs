# Operator documentation

## Overview

The datacoves _operator_ is a kubernetes [controller][], written in go,
scaffolded using [kubebuilder][]. It is responsible for setting up and
managing the kubernetes resources that make up a _workspace_ (a.k.a. an
_environment_). Each workspace has its own k8s namespace. The operator's source
code is in `src/core/operator/`.

[controller]: https://kubernetes.io/docs/concepts/architecture/controller/
[kubebuilder]: https://book.kubebuilder.io/


The operator watches a few custom resources that specify what to set up. They
are defined in `api/v1/`.

* `Workspace`: The main resource, fully describing a workspace. Parts of the
configuration are held in other resources, but the workspace references them all
and is the root of the configuration. Whenever a change to a model in the core
api database impacts a workspace configuration, the core-api's workspace.sync
task recomputes and (re-)writes the corresponding workspace k8s resource. The
operator detects the resource update and runs the reconciliation process to
apply any required changes to the kubernetes resources that compose the workspace.

* `User`: Each workspace has a set of users, and each user gets certain resources,
such as a code-server deployment.

* `HelmRelease`: Most services set up by the operator are installed using helm.
A HelmRelease specifies that a helm chart should be installed, using a certain
version and helm values.


## Background

Some useful background knowledge to have and resources to review:

### Go

* The [go spec](https://go.dev/ref/spec) is short, readable and precise. Use it.
* [Effective go](https://go.dev/doc/effective_go) and the [go FAQ](https://go.dev/doc/faq).
* Understanding go's concurrency constructs. CSP, goroutines and channels.
* Understanding that go (like C) is pass by value, so the distinction between
  struct types and pointers to structs is often important.
* Understanding that errors are values in go.
* Understanding the [context](https://go.dev/blog/context) package.
* [How controller-runtime's does logging](https://github.com/kubernetes-sigs/controller-runtime/blob/main/TMP-LOGGING.md).

### Kubernetes

* [API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)
* [API conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
* [The kubebuilder book](https://book.kubebuilder.io/)
* Understand resourceVersion and generation.
* Understand ownerReferences and finalizers.


## Implementation: Reconcilers

### Change detection and reconciliation

The entry points to our code are the `Reconcile` methods for each resource, in
`controllers/*_controller.go`. The framework [watches][] kubernetes resources to
determine when to call `Reconcile`. The `SetupWithManager` method can be used
to influence when `Reconcile` should be called.

[watches]: https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes

Reconciliation must be idempotent. If an error is returned, or there's a panic,
the framework will retry calling `Reconcile` repeatedly, less frequently each
time.

To simplify change detection and ensure deployments are restarted when a secret
or configmap that affects them changes, we treat secrets and configmaps as
immutable values. We include a hash of their contents in their names. This means
to start using the new version references to them must be updated. This implies
that resources using them will change too, which means all changes can be detected
by watching the resource that has the reference, without checking the contents
of the secret or configmap.

### Applying changes to derived resources

Reconciliation is conceptualy stateless. We compute a set of derived resources
from the current value of the Workspace resource. We would like to have a
primitive that is the equivalent of `kubectl apply` in our go code. Unfortunately
reusing that mechanism is/was not available when writing the operator so we had
to build our own resource diffing. These are the `reconcile*` functions in
`controllers/reconcilers.go`.

### Concurrency

The framework runs `Reconcile` concurrently for different resource types. It also
runs the reconciliation for different resources concurrently, at most `MaxConcurrentReconciles`
at once. Reconciliation of multiple changes to a single resource happens serially.

We take advantage of this fact to isolate failures. The Workspace reconciler
applies changes to HelmRelease and User resources. This way the reconciliaton of
a HelmRelease or a User failing won't make the whole Workspace reconciliation fail.


## Implementation: Helm runner

Before having the `helm` module carry out the installation of helm charts by
starting helm subprocesses we used to call into helm's go code directly from
the helmrelease controller. This caused two problems:

* When the operator was restarted the helm release (stored by helm in a k8s secret)
  could be left in a pending-upgrade state, which should only happen if helm is
  still running. This is due to helm not cleaning up when interrupted.
* We run out of memory, most likely due to a memory leak involving helm state.

To address these issues we implemented the `helm` module, which schedules helm
supbrocesses so that we can control their execution. It is a separate module
that runs a singleton scheduler process and receives requests to run helm over a
channel. The helmrelease_controller simply sends requests to this process
without waiting or checking results.

Currently helm install failures will be logged but won't be retried. Manual
intervention is required in this case. In any case, retrying the whole helm
install is unlikely to succeed if nothing changed. Certain kinds of intermitent
failures could be detected and retried within an operation if desired. But in
this case, not retrying the helmrelease reconciliation as a whole is best, I think.

The meat of the implementation is in the `run` function. It keeps track of
running and pending operations (and their potential memory usage) and spawns new
goroutines for each install/upgrade/uninstall operation. It is somewhat subtle
code. You should understand goroutines and channels well before touching it.

When the operator is signaled by kubernetes to exit, we must be as gentle as
possible with helm subprocesses to avoid leaving the releases in a bad state.
There's a grace period between the first signal that the program will exit
and forceful termination. We use it to send SIGTERM to all the helm subprocesses,
which should allow them to exit more cleanly than if they were SIGKILLed. We
haven't seen any more chart's left in `pending-upgrade` after this change.

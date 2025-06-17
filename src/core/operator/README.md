This directory has the kubernetes operator that manages datacoves.com/Workspace objects.

The initial directory structure was scaffolded with kubebuilder.


### Running locally

```bash
# Run the operator. It will use your kubectl config to auth with the API, and it
# runs like a normal go program, outside the cluster.
make run ENABLE_WEBHOOKS=false

# Or, to run with the delve debugger (brew install delve)
make debug ENABLE_WEBHOOKS=false
```

### Run locally in cluster

```bash
# Build the image and load it into kind.
make docker-build IMG=datacovesprivate/operator:0.3.0 && ../cli.py kind_load_version 0.3.0

# Deploy
make deploy IMG=datacovesprivate/operator:0.3.0
alias kco='kubectl -n operator-system'
kco delete pods -l control-plane=controller-manager # delete the pod to reload the image if needed

# See logs
kco logs -l control-plane=controller-manager -c manager -f
````

### Resources

* The kubebuilder book
* [Kubernetes API Conventions](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md)
* The [controller-runtime docs](https://pkg.go.dev/sigs.k8s.io/controller-runtime)
* The [controller-runtime docs about logging](https://github.com/kubernetes-sigs/controller-runtime/blob/master/TMP-LOGGING.md)
* The nginx-ingress-operator source code
* The kubernetes-operator channel on the kubernetes slack


### Recommended dev tools

* gopls editor integration

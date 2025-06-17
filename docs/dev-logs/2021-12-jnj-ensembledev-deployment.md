# Datacoves deployment

This document describes the deployment of the components of a datacoves system
to a JnJ EKS kubernetes cluster.

## Prerequisites

[This confluence page](https://confluence.jnj.com/display/AHRX/How+to+Deploy+a+new+Datacoves+cluster+-+Datacoves+-+How+to+guides)
should be followed prior to the steps outlined here to deploy datacoves. It
should document how to setup an EKS cluster with the necessary prerequisites,
and how to create and configure the required AWS services used.

We assume here that there is a EKS cluster running with certain services already
deployed on it. The cluster is setup through CI from the git repo at
https://sourcecode.jnj.com/projects/ITX-AZT/repos/ensemble.
We require the following systems running in the cluster:

* ingress-nginx as an ingress controller.
* cert-manager to issue SSL certificates.
* external-dns to create DNS rules from annotations.
* A system that creates a new kubernetes secret with a known name with
  credentials to pull docker images in every namespace of the cluster.

The machine from where the deployments scripts will be run must have python3 and
git installed, as well as kubectl (client) version 1.21 or higher, configured
to access the cluster with broad permissions.

We also assume the docker registry / repository that you configure to pull
images has all the docker images required. Datacoves will build and push this
images. The list of images used by a cluster, computed from this repo's
configuration, can be displayed with `./cli.py images ensembledev.apps.jnj.com`,
or in general `./cli.py images CLUSTER_DOMAIN`.


## Initial setup and configuration

Clone the datacoves_deployment git repository and change directory to it.

```sh
git clone https://sourcecode.jnj.com/scm/asx-ahrx/datacoves_deployment.git
cd datacoves_deployment
```

Configuration is stored in the repo, encrypted using git-secret. You will need
to be in the repo's git secret keyring to decrypt them. Ask someone already in
the keyring for access (e.g. spelufo@its.jnj.com).

Decrypt the configuration secrets. The `-f` flag will overwrite existing files.

```
git secret reveal -f
```

The `config` directory holds configuration files. Each subdirectory holds
configuration for a kubernetes cluster and must be named after the cluster
domain name. For example, the configuration for the current (2021) version of
datacoves is in `config/ensembledev.apps.jnj.com`.

If deploying to a new cluster, create a new directory under config based on
`config/ensembledev.apps.jnj.com`. You will need to use `git secret add` and
`git secret hide` to add your new secrets to the repo and encrypt them before
commiting them.


## Deploying datacoves core web application

First, make sure your kubectl context is appropiate for the cluster.

```sh
CLUSTER_DOMAIN=ensembledev.apps.jnj.com
KCTX=$(kubectl config current-context)

# Deploy the datacoves core api server to the core namespace.
./cli.py setup_core "$KCTX" "$CLUSTER_DOMAIN"
```

Enter an api server pod and run database migrations:

```sh
kubectl -n core exec -it $(kubectl -n core get pods -l app=core-api -o name) -- bash

# From inside the pod:
./manage.py migrate
./manage.py loaddata */fixtures/*
```

Check the server is running:
```
$ kubectl -n core get pods
NAME                                   READY   STATUS    RESTARTS   AGE
core-api-deployment-5f8f64cf69-6rvhd   1/1     Running   0          3d19h
```


## Deploying datacoves project operator

The datacoves project operator manages two [CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/):
datacoves.com/Project and datacoves.com/User. To deploy the operator, run:

```sh
./cli.py setup_operator "$KCTX" "$CLUSTER_DOMAIN"
```

To check the operator is running, and/or see its logs:

```
$ kubectl -n operator-system get pods
NAME                                          READY   STATUS    RESTARTS   AGE
operator-controller-manager-78cc7cfb6-9ddkw   2/2     Running   0          47h

$ kubectl -n operator-system logs -l control-plane=controller-manager -c manager -f
```


## Deploying a datacoves project namespace

Every project is deployed to a namespace named `dcp-{project_name}`. The
setup_project script creates a new namespace and project kubernetes object from
the configuration file in `config/{cluster_domain}/projects/{project_name}.yaml`.
The operator will detect changes to this object and create deployments and other
resources for the project.

```sh
PROJECT_NAME=emeadev
./cli.py setup_project "$KCTX" "$CLUSTER_DOMAIN" "$PROJECT_NAME"
```

To watch for pod status changes as the operator create's the project resources:

```sh
kubectl -n "dcp-$PROJECT_NAME" get pods --watch
```

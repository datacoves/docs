# Installation

## Set up IAM user

IAM user needs the following privileges to create the cluster:

https://eksctl.io/usage/minimum-iam-policies/

## AWS CLI

Install AWS CLI in your local environment

https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

## Configure credentials

1. Generate access key
2. Configure your credentials

## Install eksctl

Install eksctl

https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html

### On Mac

```
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl
```

## Create cluster

https://eksctl.io/usage/creating-and-managing-clusters/

```
eksctl create cluster -f cluster.yaml --tags service=datacoves
```

## Install metrics server

https://docs.aws.amazon.com/eks/latest/userguide/metrics-server.html

```
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

## Kubernetes dashboard

https://docs.aws.amazon.com/eks/latest/userguide/dashboard-tutorial.html

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.5/aio/deploy/recommended.yaml
kubectl apply -f eks-admin-service-account.yaml
```

### Open dashboard

```
kubectl proxy
```

http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#!/login

Get a login token with:

```
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep eks-admin | awk '{print $1}')
```


## Configure Docker hub

```
kubectl create ns alpha2
kubectl create secret docker-registry docker-secret \
--docker-server="https://index.docker.io/v1/" \
--docker-username="<USER_NAME>" \
--docker-password="<PASSWORD>" \
--docker-email="<EMAIL>" \
--namespace="alpha2"
```


## EKS (k8s on AWS)


```sh
# Create the cluster  https://eksctl.io/usage/creating-and-managing-clusters/
eksctl create cluster -f eks/eks-cluster.yaml

# (Optional) Inspect the config that kustomize generates
kubectl kustomize eks

# Apply the kustomization directory to the cluster
kubectl apply -k eks
```

## Kubernetes dashboard

To open the dashboard run `kubectl proxy` and navigate to:

http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#!/login

```sh
# Get a login token with
kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep eks-admin | awk '{print $1}')
```


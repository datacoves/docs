# How to configure Service Account Docker in Kubernetes for pull images.

**JnJ** and **Kenvue** are using their own private Docker artifact repositories. In order to download images from those repositories in Kubernetes we need to create secrets with valid credentials in each Kubernetes cluster.

This process is documented by JnJ at [conflunce](https://confluence.jnj.com/display/EAKB/Artifactory+-+Docker+Image+Pull+Through+Cache+For+Trusted+Public+Registries).


## Select Kubernates context

```bash
kubectl config get-contexts
kubectl config use-context <context>
```

## Delete old service account (If it already exists)

```bash
kubectl get secrets -n default
kubectl delete secret taqy-docker -n default
```

## Create new service account

```bash
# Create secret in default namespace - Recommended to use the EAT service account username and password for credentials
kubectl create secret docker-registry taqy-docker --docker-server=jnj.artifactrepo.jnj.com --docker-username=<service-account-username> --docker-password=<service-account-password> -n default
 
# Annotate secret to sync across all namespaces
kubectl annotate secret taqy-docker cluster.managed.secret="true" -n default
```

## Inspect the new secret

```bash
kubectl -n default get secret taqy-docker -o yaml
```

Copy the value from `data.dockerconfigjson`

```bash
echo <value> | base64 -d
```

Note: Check that the secrets have been replicated to all namespaces. (Can check one or two)

```
kubectl -n <namespace> get secret taqy-docker -o yaml
echo <value> | base64 -d
```

If the secret was not replicated, check the pod's logs:

```bash
kubectl -n kube-system get pods
kubectl -n kube-system logs namespace-secrets-sync-<hash> --tail 100
```
# Administrate east-us-a AKS cluster

## Permissions

1. Ask an administrator to create you a datacoves (microsoft) user. https://admin.microsoft.com.
2. Ask an administrator to add you to the `DevOps` [group](https://portal.azure.com/#view/Microsoft_AAD_IAM/GroupDetailsMenuBlade/~/Members/groupId/3debb9f2-c29e-4485-81c7-d4644d359d1b).

## Configure kubectl

[Download Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

Login to your account:

```bash
az login
```

Then, run the following commands:

```bash
az account set --subscription 91bd2205-0d74-42c9-86ad-41cca1b4822b
az aks get-credentials --resource-group datacoves --name east-us-a
```

This will add a new context to `kubectl`, so you can now run:

```bash
kubectl get pods -A
```

## Manage nodepools

### List nodepools

List nodepools in the `datacoves` resource group, `east-us-a` cluster:

```sh
az aks nodepool list --cluster-name east-us-a --resource-group datacoves
```

### Add workers nodepool

```sh
 az aks nodepool add --cluster-name east-us-a --resource-group datacoves --name workerslarge --mode User --enable-cluster-autoscaler --min-count 1 --max-count 10 --node-vm-size Standard_D4s_v3 --labels k8s.datacoves.com/workers=enabled
```

## Modify existing nodepool to add new labels

Let's add a new label `k8s.datacoves.com/workers=enabled` to an existing nodepool which already has the label `k8s.datacoves.com/nodegroup-kind=general`. Old a new labels need to be specified.

```sh
az aks nodepool update --cluster-name east-us-a --resource-group datacoves --name generallarge --labels {k8s.datacoves.com/workers=enabled,k8s.datacoves.com/nodegroup-kind=general} 
```
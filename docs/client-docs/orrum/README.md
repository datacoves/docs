
# Datacoves deployment

This section contains instructions on how to connect to Orrum infra via azure to build, maintain, and monitor datacoves deployments.

# VPN Connection

kubectl requires connection to Orrum VPN. Download [Azure VPN Client](https://apps.apple.com/us/app/azure-vpn-client/id1553936137?mt=12). 

The profile can be downloaded from Azure; login with Support_Datacoves@orrumcorp.onmicrosoft.com with the credentials from 1Password.

https://portal.azure.com/#@orrum.com/resource/subscriptions/0f8e4c48-c319-4ed9-af14-ef50501e3a41/resourceGroups/DataCoves/providers/Microsoft.Network/virtualNetworkGateways/DataCovesGateway/pointtositeconfiguration

Click "Download VPN client" in the header, and you will get a zip file with the profile files; you will want the Azure client profiles, and you can use the Import button in the Azure client to import it.


To connect to the vpn, use Support_Datacoves@orrumcorp.onmicrosoft.com, credentials on 1Password.

## kubectl setup

```shell
# Ensure Python is Installed
pipx install az-cli --include-deps

# Get login password from 1pswd
az login -u Support_Datacoves@orrumcorp.onmicrosoft.com

# Install kubectl + kubelogin
az aks install-cli

# Set subscription
az account set --subscription 0f8e4c48-c319-4ed9-af14-ef50501e3a41

# Get credentials for new cluster
az aks get-credentials --resource-group DataCoves --name Datacoves_kube

# List contexts
kubectl config use-context Datacoves_kube
```

## Rename Context

It is very important that the context be named orrum-new as things such as updating the cluster will have scripts that depend on the context name.

```
kubectl config rename-context Datacoves_kube orrum-new
kubectl config use-context orrum-new
```

Now verify connectivity with `kubectl get ns`

## Config DNS on `/etc/hosts` (Optional)

Note: This is probably not necessary anymore.

You can force the domain and subdomains DNS if it's not configured.

```
10.10.0.36       datacoves.orrum.com
10.10.0.36       api.datacoves.orrum.com
10.10.0.36       authenticate-dev123.datacoves.orrum.com
10.10.0.36       dev123.datacoves.orrum.com
10.10.0.36       airbyte-dev123.datacoves.orrum.com
10.10.0.36       dbt-docs-dev123.datacoves.orrum.com
10.10.0.36       airflow-dev123.datacoves.orrum.com
10.10.0.36       superset-dev123.datacoves.orrum.com
10.10.0.36       grafana.datacoves.orrum.com

# <user>
10.10.0.36       <user>-1-transform-dev123.datacoves.orrum.com
10.10.0.36       <user>-1-dbt-docs-dev123.datacoves.orrum.com
10.10.0.36       <user>-transform-dev123.datacoves.orrum.com
```

*Note: Check the cluster's Public IP `10.10.0.36`*

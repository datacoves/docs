# Infra notes

## Create service user

This is only if you are creating a brand new environment.

```
az ad sp create-for-rbac --name DatacovesAutomatedDeployment --role Contributor --scopes /subscriptions/91bd2205-0d74-42c9-86ad-41cca1b4822b
```

## Set up Azure credentials

This should be made by the secret reveal probably.

```
mkdir ~/.azure
vi ~/.azure/credentials
```

Put in the file (comes from az command above):

```
[default]
subscription_id=xxx
client_id=xxx
secret=xxx
tenant=xxx
```

## Install requirements

```
pip install ansible==2.18.2
ansible-galaxy collection install azure.azcollection --force
pip3 install -r ~/.ansible/collections/ansible_collections/azure/azcollection/requirements.txt
```

## Environment variables used

```
# REQUIRED for AZ deployment: (these come from the az command above)
export DC_AZ_SERVICE_CLIENT_ID=xxx
export DC_AZ_SERVICE_CLIENT_SECRET=xxx

OPTIONAL for AZ deployment:
export DC_AZ_AKS_NAME=datacoves-test
export DC_AZ_RESOURCE_GROUP=DatacovesTesting
export DC_AZ_LOCATION=eastus
export DC_AZ_KUBERNETES_VERSION=1.31.5


OPTIONAL for DC deployment:
export DC_RELEASE=3.3.202502202042  or latest
export OP_SERVICE_ACCOUNT_TOKEN=...
export DC_SKIP_REVEAL_SECRETS=1
export DC_HOSTNAME=datacoves-test.datacoves.com
export DC_KUBECTL_CONTEXT=...


export DC_SENTRY_DSN_OPERATOR="https://b4d54fe4d14746729baa351a2d3bf4f9@o1145668.ingest.sentry.io/4504730556170240"
export DC_SENTRY_DSN="https://5d7d4b6b765d41a295ba80e70d685cf2@o1145668.ingest.sentry.io/6213267"
export DC_SLACK_TOKEN="xxx"
```

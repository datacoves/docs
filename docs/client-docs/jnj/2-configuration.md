# Configuring datacoves

Configuration for each cluster is kept in a separate repository. They are
mounted as git submodules under `config/{cluster_domain}`.

You will need to create this git repository if there isn't one already for your
cluster. Grant access to datacoves staff to this repo so we can initialize the
configuration files and add the people that will do configuration or deployment
to the git secret keyring.

Clone this configuration to make changes to it. Alternatively, if you will run
the datacoves deployment from the same machine you can clone the datacoves_deployment
repository which has the configuration repos as [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules).

```bash
git clone https://sourcecode.jnj.com/scm/asx-ahrx/datacoves_deployment.git
cd datacoves_deployment
git submodule init
git submodule update config/$cluster_domain  # Specify the path to the submodule to update.
cd config/$cluster_domain # Config repo cloned as submodule in here.
```

After the initial setup, the workflow to update configuration is as follows:

```bash
# From within the cluster configuration repo.

# 1. Fetch the latest configuration.
git checkout main
git pull
git secret reveal -f

# 2. Make your changes (see below what's required).

# 3. Commit and push your changes.
git secret hide
git diff # Review your changes, all sensitive data should be encrypted.
git add .
git commit -m 'Updated secrets/configuration.'
git push
```

## What values are required?

Initially the configuration files will contain `TODO` comments to mark the
places where values need to be filled in. Run `grep -r . TODO` to see what's
pending. Remove the `TODO` comments when you add a value. Most values are used
to configure the external services that were created during[cluster setup](./1-cluser-requirements.md).

The configuration variable names should give you an indication of what's needed.
If in doubt, ask.

The requirements for each datacoves service follow. The list may be a useful
guide but it could be out of date. Please rely on the `TODO` marks, not on the
list, as authoritative information.

### Datacoves core

- Datacoves api DB host (`DB_HOST`) and password (`DB_PASS`) in `secrets/core-api.env`
- PING_CLIENT_ID and PING_CLIENT_SECRET in `secrets/core-api.env`
- Ping group names in `cluster-params.yaml`, under `project`.
- Postgres DB Provisioner for services such as airbyte/airfow/superset in `cluster-params.secret.yaml` under `postgres_db_provisioner`.

### DBT Docs

- Deploy credentials in `cluster-params.secret.yaml` under `deploy_credentials`.

### Airbyte

Not yet documented.

### Airflow

The EFS CSI driver installed by cloudx is usually outdated (v1.0.0) so we need to opt out from the cloudx managed service.

To do so, submit a PR to have Cloudx stop managing the currently installed driver here: https://sourcecode.jnj.com/projects/ITX-AED/repos/cloudx_container_pipelines_configs/browse/argocd/config.yaml#19


- Airflow EFS volume_handle (fs id) in: `environments/dev123/airflow.secret.yaml`

### Superset

Not yet documented.

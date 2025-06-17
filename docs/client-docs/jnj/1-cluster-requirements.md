# Datacoves cluster requirements

[Summary for the requirements of a new Cluster.](./8-summary-requirements-new-cluster.md)

## EKS cluster

The clusters are created through CloudX pipelines, from `cluster.yaml` files ([docs](https://confluence.jnj.com/display/AGAP/Deploying+VPCx+EKS+Cluster)).
For every cluster there's a git repository with the cluster definition. If your
team create one of this repositories, please either grant access to datacoves staff so
we can make changes if required or ask us to check your `cluster.yaml`.

An example repository of this kind is [itx-ank/ensemble](https://sourcecode.jnj.com/scm/itx-ank/ensemble).

Important configuration to take into consideration:

- Kubernetes version: latest confirmed working version.  This is either -1 or -2 releases from current based on the time of year.
- Addons versions
- Worker groups: general, volumed, and workers.

### Cluster configuration files

| Cluster          | Repository                                                                                 | Branch      |
|------------------|--------------------------------------------------------------------------------------------|-------------|
| Ensemble test    | https://sourcecode.jnj.com/projects/ITX-ANK/repos/ensemble/browse/_scm_cluster             | test        |
| Ensemble         | https://sourcecode.jnj.com/projects/ITX-CCC/repos/ensemble/browse/_scm_cluster             | production  |
| R&D              | https://sourcecode.jnj.com/projects/ITX-BHE/repos/integrationscluster/browse/_scm_cluster  | test        |
| Artemis Dev      | https://sourcecode.jnj.com/projects/ITX-ADW/repos/artemiseks/browse/_scm_cluster           | development |
| Artemis          | https://sourcecode.jnj.com/projects/ITX-ADW/repos/artemiseks/browse/_scm_cluster           | production  |
| Chap development | https://sourcecode.jnj.com/projects/ITX-WCR/repos/datacove/browse/_scm_cluster             | development |
| Chap production  | https://sourcecode.jnj.com/projects/ITX-WCR/repos/datacove/browse/_scm_cluster             | production  |

Once the cluster was provisioned, you'll receive an e-mail containing the details to configure `kubectl`. Please forward to the datacoves team.

The installer will need kubectl access to the cluster [docs](https://confluence.jnj.com/display/AGAP/EKS+RBAC+Overview). 

### Opt out from EFS CSI driver 

The EFS CSI driver installed by cloudx is usually outdated (v1.0.0) so we need to opt out from the cloudx managed service.

To opt out from EFS CSI managed driver, create a pull request on this repo, similar to this [one](https://sourcecode.jnj.com/projects/ITX-AED/repos/cloudx_container_pipelines_configs/pull-requests/257/diff#argocd/config.yaml).

### External DNS

In the cluster.yaml configuration there is a key `external_dns`. This key deploys the service [External DNS](https://github.com/kubernetes-sigs/external-dns) to the cluster, managed by CloudX.
This service might not be available in some clusters yet, so a manual configuration might be needed on Route53 or any other DNS service, typically a CNAME record pointing to the cluster's load balancer hostname.

#### Getting load balancer's hostname

```shell
kubectl -n ingress-nginx get svc ingress-nginx-controller -o=jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### SSL Certificates Manager

CloudX will install [Cert Manager](https://cert-manager.io/) if the cluster supports it.

If Cert Manager is not installed, 2 SSL certificates need to be issued manually:
- wildcard certificate: *.[SUBDOMAIN].[DOMAIN]
- root certificate: [SUBDOMAIN].[DOMAIN]

A certificate chain file and a Private key are required for each certificate, please send the 4 files to Datacoves staff.

## Git repositories 

### Config repo 

Each datacoves installation requires a configuration repo where Datacoves staff will store configuration details. 

Please create one repo per kubernetes cluster and grant access to Datacoves staff. 

### Dbt analytics repo 

This is the repo where your analytics (dbt) project resides, along with airflow dags, db security roles, documentation, etc. 

### Git Service Account 

Please create a Service Account with read access to the analytics repo, since that service account will be configured on services like Airflow and dbt-docs to read files from the repo. 

To do so, submit a PR to have Cloudx stop managing the currently installed driver here: https://sourcecode.jnj.com/projects/ITX-AED/repos/cloudx_container_pipelines_configs/browse/argocd/config.yaml#19

This account will be also used by Jenkins to download images from artifactory (taqy-docker namespace), so please request access to `taqy-docker` on that account via AppDevTools.

## Database

Some services require Postgres databases, as described below. These databases can share an RDS instance or aurora cluster. You will need to create this database cluster/instance and ensure it can be accessed from the EKS cluster. 

### Minimum requirements

- Engine: Postgres
- Version: 14.9
- Multi-AZ: "Single DB Instance" for sandbox clusters, "Multi-AZ DB Cluster" if not.
- Master user: postgres
- Master password: <PASSWORD>
- Instance class: db.r5.large
- Storage type: Aurora Standard or gp2
- Allocated_storage: 100GB
- Enable storage autoscaling
- Maximum storage threshold: 1TB
- Authentication: password

Keep in mind that JNJ cycles the master password every 24 hours so you need to run any setup command using this password before that happens.

### Initial database and user

You'll need to create a master Postgres user and the datacoves database:

```SQL
CREATE USER datacoves PASSWORD insert_generated_random_password_without_special_characters;
ALTER USER datacoves CREATEDB CREATEROLE;
GRANT datacoves TO postgres;
CREATE DATABASE datacoves OWNER datacoves;
REVOKE connect ON DATABASE datacoves FROM PUBLIC;
GRANT connect ON DATABASE datacoves TO datacoves;
GRANT connect ON DATABASE datacoves TO postgres;
```

A way to generate passwords: `python -c 'import secrets; print(secrets.token_urlsafe())'`.
Avoid special characters, they cause issues with some services, such as airflow.

Please share this password with the Datacoves team.

## Active Directory groups

Roles/groups required for datacoves users:

```
JNJ-APP-{division}-DATACOVES-ADMIN
JNJ-APP-{division}-DATACOVES-DEVELOPER
JNJ-APP-{division}-DATACOVES-VIEWER
JNJ-APP-{division}-DATACOVES-KTLO
```

Substitute your `{division}`, e.g. `PCE`, `HMD`, `CHAP`, etc.

## Ping identity account

Submit a ticket to [Web Single Sign-On - SAML Federation](https://jnjprod.service-now.com/iris?id=sc_cat_item&sys_id=8fa9a4a4f88c81402b7d832c9cb96435&sysparm_category=a96e3c1f1d7ff100b7633835df15e2d1)
to create a ping account.

### IRIS Request

#### Short Description

This is a request to enable SSO for <APPLICATION> cluster.

#### Description

Need to add PingID to application.

#### Groups

Need groups only filtered to ones that have the following pattern JNJ-APP-<division>-DATACOVES-\*

#### Type

Choose: OAuth/OpenID Connect

#### Client id

It should be any name for your cluster (e.g. `chapsbx`, `emea_ensemble_test`, `emea_artemis_dev`, etc.).

#### Redirect urls

`https://api.{cluster_domain}/complete/ping_federate`

#### Additional fields

Requires interactive electronic signatures using SSO: No
Attributes: groups, openid, profile, email

When the Iris request is fulfilled, you will receive an email with:

- Client ID (verify this is the one that was requested)
- Client Secret
- A list of OAuth endpoints

Please share this information with the Datacoves team.

## Airflow

### EFS file system for airflow logs

Follow the instructions to "Create EFS in AWS Account" from [this confluence page](https://confluence.jnj.com/display/AGAP/AWS+EFS+Persistent+Storage+-+AWS+EFS+CSI+Driver). Don't follow the other sections of the page.

As a name use datacoves-[cluster id]-[environment slug]-airflow-logs.

It's important to attach the right the EKS security group so the EKS cluster has access to the EFS filesystem. You can find the security group id in the EKS cluster admin page, Networking tab, under `Additional security groups`.

### S3 bucket for Airflow dags

Due to bitbucket scheduled downtimes we recommend using S3 as the DAGs store to mimimize disruptions.

1. Create an S3 bucket per environment, i.e. datacoves-[cluster id]-[environment slug]-airflow-dags (datacoves-ensemble-pro001-airflow-dags)
2. Create an IAM policy that grants read/write access to the new S3 bucket created, use the same name convention used for the S3 bucket.
3. Follow [this instructions](https://confluence.jnj.com/display/AGAP/AWS+IAM+Roles+for+Kubernetes+Service+Accounts) to create an IAM Role, up to "Create IAM Role For K8s Service Account", attach the policy you created on step 2. Name the IAM role using the same convention you used for the S3 bucket
4. Do not associate the IAM role to a K8s Service Account, that part is managed by Datacoves.
5. Create a IAM user for jenkins to upload the dbt project and dags to S3. Use the same naming convention. Attach the same policy you created on step 2.

#### Trusted policy example:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::327112934799:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/125EA29C302DF7DBB900ED84AA85F0BB"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "oidc.eks.us-east-1.amazonaws.com/id/125EA29C302DF7DBB900ED84AA85F0BB:sub": "system:serviceaccount:dcw-dev123:dev123-airflow-*",
                    "oidc.eks.us-east-1.amazonaws.com/id/125EA29C302DF7DBB900ED84AA85F0BB:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
```

## DBT API

- Create an S3 bucket.
- Choose a bucket name, we suggest using <cluster_id>_dbt_api where <cluster_id> could be `ensemble`, `ensembletest`, etc.
- Create an IAM user with a policy to access the bucket, like the one below,
  replacing `{your_bucket_name}` with your bucket's name.
- Create an access key for the user. Share it with the Datacoves team.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "arn:aws:s3:::{your_bucket_name}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::{your_bucket_name}"
    }
  ]
}
```

## Grafana

Grafana requires an S3 bucket with lifecycle management enabled.
Follow [this guide](grafana-loki-storage-config-providers.md) to configure it accordingly.

## Airbyte

- S3 bucket for airbyte logs, an IAM user with a policy to access it, and an
  access key for the user.

### S3 bucket for airbyte logs

- Create an S3 bucket.
- Create an IAM user with a policy to access the bucket, like the one below,
  replacing `{your_bucket_name}` with your bucket's name.
- Create an access key for the user. Share it with the Datacoves team.

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "arn:aws:s3:::{your_bucket_name}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::{your_bucket_name}"
    }
  ]
}
```

## Data warehouse connection templates 

Please define how your data warehouse architecture will look and define the connection templates for both Analytics Engineers and Services, I.e. on a Snowflake database you’ll need to specify fields such as account, warehouse, database, role.

## Terraform

Some work has been done (repo: [itx-azt/iac][iac]) to automate the creation of
these cluster requirements using terraform. However, because of authorization
restrictions imposed on terraform in jnj, it still requires manual
intervention. At the moment it is probably faster overall to do everything
manually.

[iac]: https://sourcecode.jnj.com/projects/ITX-AZT/repos/iac

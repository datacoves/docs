# Summary for the requirements of a new Cluster.

For more details check [Cluster requirements](./1-cluster-requirements.md)

## Database (RDS)

### Minimum requirements

- Engine: Postgres
- Version: 14.9
- Multi-AZ DB Cluster.
- Master user: postgres
- Master password: <PASSWORD>
- Instance class: db.r5.large
- Storage type: Aurora Standard or gp2
- Allocated_storage: 100GB
- Enable storage autoscaling
- Maximum storage threshold: 1TB
- Authentication: password


## EKS

### Configuration

- External DNS.
- `m5.xlarge` instances.

### Worker groups

* General
* Volumed
* Workers

#### General

- min_nodes: 1
- max_nodes: 30
- root_volume_size: 200
- labels:

```yaml
labels:
    ...
    - key: k8s.datacoves.com/nodegroup-kind
    value: general
```

#### Volumed

- min_nodes: 1
- max_nodes: 30
- root_volume_size: 200
- labels:

```yaml
labels:
    ...
    - key: k8s.datacoves.com/nodegroup-kind
    value: volumed
```

#### Workers

- min_nodes: 1
- max_nodes: 30
- root_volume_size: 200
- labels:

```yaml
labels:
    ...
    - key: k8s.datacoves.com/workers
    value: enabled
```


## Other configuration.

- EFS for each environment for **Airflow Logs**.
- S3 buckets for each environment for **Dags sync**, with read-only permissions. (Optional. Can be git-sync).
- One S3 bucket for **Observavility stack**. Example `ensemble-prd-observability-grafana-loki`. (Full permissions)
- One S3 bucket for **dbt-api**. Example `ensemble-prd-dbt-api`. (Full permissions)


### Example for full S3 bucket permission

```json
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
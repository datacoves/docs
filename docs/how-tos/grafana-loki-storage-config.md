# Grafana Loki Storage Configuration

There are three different providers to configure **Loki** storage:

- AWS S3
- Azure Blob Storage
- Minio (Local development)

## Notes

 - Minio is not responsible for log rotation, the logs lifecycle must be configured in your provider.
 - How to configure the provider? [here](grafana-loki-storage-config-providers.md)

To configure the cluster you must add the configuration to the configuration repository as a secret in `<domain>/cluster-params.secret.yaml`
for example to our local environment `datacoveslocal.com/cluster-params.secret.yaml`

## Minio (Local development)

```shell
grafana:
  ...
  loki:
    provider: minio
    password: ...
```

## AWS S3

```shell
grafana:
  ...
  loki:
    provider: aws
    region: <us-east-1>
    access_key: ...
    secret_key: ...
    bucket: <bucket-name>
```

## Azure Blob Storage

```shell
grafana:
  ...
  loki:
    provider: azure
    account_name: ...
    account_key: ...
    container_name: <container-name>
    endpoint_suffix: <blob.core.windows.net>
```

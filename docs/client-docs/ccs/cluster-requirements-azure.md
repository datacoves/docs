# Summary for the requirements of a new Cluster.

## Database (Azure Database for PostgreSQL - Flexible Server)

### Minimum requirements

- Version: 14 or later
- Workload Type: Production
- Compute+Storage: General Purpose, D4ds_v5
- Geo-Redundancy and High Availability optional but recommended.
- Admin user/password required and must be provided to Datacoves.
- Storage Type: Premium SSD
- Storage Size: 128 GiB
- Performance Tier: P10
- Storage auto growth enabled optional but recommended.

## Kubernetes Services

### Configuration

- Kubernetes version: 1.30.6 or later

### Node pools
* general 
* volumed
* workers - Standard_D4s_v3 node, 128 gig OS disk size

### Worker groups

* General
* Volumed
* Workers

#### General

- Standard_D4s_v3
- min_nodes: 1
- max_nodes: 4
- root_volume_size: 128
- labels:

```yaml
labels:
    ...
    - key: k8s.datacoves.com/nodegroup-kind
    value: general
```

#### Volumed

- Standard_D16s_v5
- min_nodes: 1
- max_nodes: 4
- root_volume_size: 512
- labels:

```yaml
labels:
    ...
    - key: k8s.datacoves.com/nodegroup-kind
    value: volumed
```

#### Workers

- min_nodes: 1
- max_nodes: 4
- root_volume_size: 128
- labels:

```yaml
labels:
    ...
    - key: k8s.datacoves.com/workers
    value: enabled
```


## Other configuration.

#### SSL Certificate

We recommend using a wildcard certificate, however we can also use cert manager for free certificates if that is the preference.

Certificates must be issued for:

- `*.domain.com`
- `domain.com`

Where 'domain.com' is whatever base domain you wish to use.  We recommend using "datacoves.YOUR_DOMAIN.YOUR_TLD", such as 'datacoves.mycompany.com'.  In such a case, you would need certificates for:

* `*.datacoves.mycompany.com`
* `datacoves.mycompany.com`

#### DNS Configuration

Either DNS must be configured to support the same wildcard and base domain, or the cluster must be allowed to create DNS entries via kubernetes' external-dns annotation.

# Useful prometheus queries

## node status with pressure

```promql
sum by(node) (kube_node_status_condition{status="true", condition="DiskPressure"}) +
sum by(node) (kube_node_status_condition{status="true", condition="MemoryPressure"}) +
sum by(node) (kube_node_status_condition{status="true", condition="PIDPressure"})
```

## pods memory filtering by pod name with regex

```promql
sum by(pod) (container_memory_usage_bytes{namespace="<NAMESPACE>", pod=~"<PREFIX>.*"})
```

## containers cpu usage by node

```promql
sum by(node) (rate(container_cpu_usage_seconds_total{node="<NODE>"}[5m]))
```

## Node memory

```promql
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100
```

## Loki ingester chunk stored size

```promql
loki_ingester_chunk_stored_bytes_total{job="loki"}
```

## Pods killed bec exceeding memory limit

```promql
sum by(pod) (kube_pod_container_status_terminated_reason{reason="OOMKilled", namespace="dcw-prd001"})
```

## Total worker nodes (measued by nodes running airflow worker pods)

```promql
count (sum by (node) (kube_pod_info and on (pod) kube_pod_labels{label_airflow_worker!=""}) > 0)
```
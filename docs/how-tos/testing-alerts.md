# How to create and test alerts

## Stack

- Alert Manager
- Loki Alert Ruler
- Grafana

## Test Loki Alert

1. Add the new alert on `scripts/data/loki-rules.yaml` file.
2. Install `Observability Stack`.
3. Force some logs.

Example: 

```bash
# Option 1
kubectl -n core exec -it api-75567b8958-7b7rx -- bash

# Option 2
./cli.py pod_sh

./manage.py shell_plus
```

```python
import requests
import time

payload = {
  "streams": [
    {
      "stream": {
        "agent_hostname": "eventhandler",
        "job": "test",
        "namespace": "core"
      },
      "values": [[ str(int(time.time() * 1e9)), "max node group size reached" ]]
    }
  ]
}

requests.post(
  url="http://loki-loki-distributed-gateway.prometheus.svc.cluster.local/loki/api/v1/push",
  json=payload,
  headers={"Content-Type": "application/json"}
)
```

4. Now you can see the alert on `Cluster Alerts`

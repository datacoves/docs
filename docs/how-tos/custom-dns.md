# About this Documentation
Some customers (like Orrum) require a custom internal DNS.  This will require adding a new coredns custom config map:

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: kube-system
data:
  sftp.orrum.com.server: |
    sftp.orrum.com:53 {
        forward . 172.31.150.10 172.31.160.20
    }
```

Change 'sftp.orrum.com' to whatever pattern needs to go to the custom DNS, and the IP addresses to the addresses of the DNS servers to resolve the address.

Then you can patch the coredns deployment:

```
kubectl -n kube-system patch deployment coredns \
  --type='json' \
  -p='[
    {
      "op": "add",
      "path": "/spec/template/spec/volumes/-",
      "value": {
        "name": "custom-coredns",
        "configMap": {
          "name": "coredns-custom"
        }
      }
    },
    {
      "op": "add",
      "path": "/spec/template/spec/containers/0/volumeMounts/-",
      "value": {
        "name": "custom-coredns.server",
        "mountPath": "/etc/coredns/custom"
      }
    }
  ]'
```

Then restarts the deployment:

```
kubectl rollout restart deployment coredns -n kube-system
```

And test with nslookup:

```
kubectl -n core exec -ti workbench-c6599969b-k4p5w -- nslookup sftp.orrum.com
```
## Resetting Datahub

Datahub uses PostgreSQL, ElastiCache, and Kafka.  If any of these three things gets out of sync for any reason, Datahub will behave very strangely.  For instance, it will claim secrets exist but not show them up in the UI.

In such an event, you will need to reset Datahub.  This can be done with the following steps:

In all these examples, replace **xxx** with the slug (such as dev123).

### Turn Off Datahub

Go to the environment you wish to reset, and disable Datahub.  Save and sync the environment and wait until Datahub come offline by monitoring the Datahub pods:

```
kubectl get pods -n dcw-xxx | grep datahub
```

This will take awhile.

### Delete Metadata in PostgreSQL

```
./cli.py pod_sh
./manage.py dbshell
\c xxx_dh
drop table metadata_aspect_v2
```

### Delete Persistent Volume Claims

```
kubectl delete pvc -n dcw-xxx elasticsearch-master-elasticsearch-master-0
kubectl delete pvc -n dcw-xxx data-xxx-kafka-broker-0
kubectl delete pvc -n dcw-xxx data-xxx-kafka-zookeeper-0
```

### Verify Persistent Volumes are deleted

```
kubectl get pv -n dcw-xxx | grep xxx | grep elasticsearch
kubectl get pv -n dcw-xxx | grep xxx | grep kafka
```

These should show no results.  These should delete automatically when the PVC is deleted, make sure they are gone.

### Re-enable Datahub

Go back to the environment, turn Datahub back on, and re-sync.


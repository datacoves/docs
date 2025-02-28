# Monitor git sync or s3 sync failure

This how-to will walk you through the steps to view git sync/s3 failures in Grafana.

### Step 1

A user with Grafana access can navigate to the Grafana UI by clicking on the Eye icon in the top right corner of the Datacoves UI.

![Grafana icon](assets/grafana-eye.jpg)

### Step 2

Navigate to `Alerting` and select `Alerting rules`.

<img src="/how-tos/metrics-and-logs/assets/grafana-alerting-menu.jpg" alt="Grafana Alerting Menu" width="300" height="600">


### Step 3

Expand the folder under `Mimir/Cortex/Loki` and select the `view` icon on the `AirflowWorkerFailedToInit` rule.

![Grafana view](assets/grafana-view.jpg)

### Step 4

Select `View in Explorer` to see the Graph and other information. 

![View in Explorer](assets/grafana-view-in-explorer.jpg)
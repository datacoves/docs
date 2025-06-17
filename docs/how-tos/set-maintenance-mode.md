# How to set the cluster in "Maintenance Mode"

Turning it on:

```
./cli.py set_maintenance_mode <kubectl context> <cluster domain> "on" "today at 9PM UTC" "support@datacoves.com" "our Support Team"
```

Turning it off:

```
./cli.py set_maintenance_mode <kubectl context> <cluster domain> "off"
```

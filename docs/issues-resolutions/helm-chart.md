# Helm Chart Resolutions

## How to patch releases?

Sometimes we want to change a value in the `Helm Chart`, but to do this we need to edit some component such as an **adapter** or the **Operator** and generate a new release, so this functionality is very useful to be able to skip that whole process and do our tests more quickly.

### Option No.1

1. Get the values from the release.

```sh
# helm get values <release> -n <namespace>
helm get values dev123-datahub -n dcw-dev123 > values.yaml
```

2. Edit/add the values to the file.

```sh
vi values.yaml
```

3. Add the repository if does not exists.

```sh
# helm repo add <name> <url>
helm repo add datahub https://helm.datahubproject.io/
```

4. Patch the helm chart.

```sh
# helm upgrade --version <x.x.x> -f values.yaml <release> <repository> -n <namespace>
helm upgrade --version 0.4.16 -f values.yaml dev123-datahub datahub/datahub -n dcw-dev123
```

### Option No.2

1. Patch the helm chart.

```sh
# helm upgrade <release> <chart> -n <namespace> --set key1=value1,key2=value2
helm upgrade dev123-datahub datahub/datahub -n dcw-dev123 --set key1=value1,key2=value2
```

[More info](https://www.baeldung.com/ops/kubernetes-update-helm-values)
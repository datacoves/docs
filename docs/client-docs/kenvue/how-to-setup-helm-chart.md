# How to set up Helm Chart on kenvue

Artifacory: https://kenvue.jfrog.io
Repository: dco-helm
Credentials: See 1password
Protocol: OCI

Steps:

1. Artifactory login.
2. Download or build the helm chart.
3. Upload the new helm chart.
4. Check the new helm chart.
5. Install the helm chart.

## 1. Artifactory login

```bash
helm registry login https://kenvue.jfrog.io/dco-helm
```

## 2. Build or download the helm chart.

In this case as an example we are going to download a helm chart from the JnJ artifactory

```bash
wget --user <my-user> --password <my-password> https://artifactrepo.jnj.com:443/artifactory/jnj-helm-charts/metrics-server-3.12.2.tgz
```

## 3. Upload the new helm chart.

```bash
 helm push metrics-server-3.12.2.tgz oci://kenvue.jfrog.io/dco-helm/metrics-server
```

## 4. Check the new helm chart.

```bash
helm show all oci://kenvue.jfrog.io/dco-helm/metrics-server
```

## 5. Install the helm chart.

```bash
helm install my-release oci://kenvue.jfrog.io/dco-helm/metrics-server --version 3.12.2
```

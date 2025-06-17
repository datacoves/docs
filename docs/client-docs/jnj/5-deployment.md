## How to deploy (or update) datacoves to a kubernetes cluster

Prerequisites: [cluster and external resources setup](./1-cluster-requirements).

SSH into a machine with kubectl access to the cluster from where you will run
the installation scripts. Then:

```bash
# Set these as needed for your cluster.
cluster_domain=FILL_IN   # e.g. ensembletest.apps.jnj.com
kubectl_context=FILL_IN  # e.g. itx-ank-ensemble-test

# Clone the repository into the installation workstation (required once).
git clone https://sourcecode.jnj.com/scm/asx-ahrx/datacoves_deployment.git
cd datacoves_deployment

# Install python dependencies for the installation scripts (required once).
pip3 install --user -r requirements.txt

# Fetch the latest changes and reveal the secrets in the config submodule directory.
git pull
git submodule update --init
(cd config/$cluster_domain; git secret reveal -f)

# Install datacoves base dependencies into the cluster (ingress-nginx, etc.)
# Usually not required after the first time datacoves is released to a cluster.
./cli.py setup_base $kubectl_context $cluster_domain

# Deploying ingress-nginx will create an ELB. Use the following command to retrieve it's URL.
kubectl --context $kubectl_context get -A svc | grep LoadBalancer

# Update cluster-params.yaml setting external_dns_url to that URL.
$EDITOR config/$cluster_domain/cluster-params.yaml
# Commit the change.

# Install/update datacoves.
./cli.py install
```

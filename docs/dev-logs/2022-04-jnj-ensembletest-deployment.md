## Datacoves deployment

This repository contains the datacoves installation scripts. They install datacoves to an existing EKS cluster, based on the configuration files in the `config` directory. Configuration for each cluster is kept in a separate repository. They are mounted as git submodules under `config/{cluster_domain}`.

Prior to this, the EKS cluster and other required AWS resources must be created. The clusters are created through CloudX pipelines, from `cluster.yaml` files in other repositories like [itx-ank/ensemble](https://sourcecode.jnj.com/scm/itx-ank/ensemble). Additional AWS resources are created using terraform from the [iac](https://sourcecode.jnj.com/projects/ITX-AZT/repos/iac) repository.

Once these prerequisites are done, and the configuration repository for the cluster has been updated accordingly, the installation is as follows.


```bash
# Set these as needed for your cluster.
cluster_domain=ensembletest.apps.jnj.com
kubectl_context=itx-ank-ensemble-test

# Clone this repository into the installation workstation.
git clone https://sourcecode.jnj.com/scm/asx-ahrx/datacoves_deployment.git
cd datacoves_deployment
git submodule update --init

# Reveal the secrets in the config submodule directory.
(cd config/$cluster_domain; git secret reveal -f)

# Install python dependencies for the installation scripts.
pip3 install --user -r requirements.txt

# Install datacoves base dependencies into the cluster (ingress-nginx, etc.)
./cli.py setup_base $kubectl_context $cluster_domain

# Install datacoves.
./cli.py install $kubectl_context $cluster_domain
```

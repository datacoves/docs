# Datacoves deployment

This repository contains the datacoves installation scripts. They install
datacoves to an existing EKS cluster, based on the configuration files in the
`config` directory. Configuration for each cluster is kept in a separate
repository. They are mounted as git submodules under `config/{cluster_domain}`.

Before running the installation scripts the EKS cluster and other required AWS
resources must be created. See [cluster requirements](./1-cluster-requirements.md).

Then a repository to use as the cluster configuration submodule must be created.
See [configuration](./2-configuration.md).

After that, deployment can begin. See [deployment](./3-deployment.md).

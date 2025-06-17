## Make a new release

To make a new release, from your development machine:

```bash
cluster_domain=ensembletest.apps.jnj.com

# Generate a new release.
git checkout main
git pull

#  Check that images are properly created in Github Actions
./cli.py generate_release
release= # The name of the release just generated.

# [If release is targeted to a submodule customer]
#   Check if any there's any config change requirement
./cli.py combined_release_notes     # Inspect the output to check for configuration changes

# Update the cluster configuration to reference the new release.
./cli.py set_release
cd config/$cluster_domain/
git secret reveal -f # Only required if you modified secrets.
change configuration as required # Only required if you modified secrets.
git secret hide      # Only required if you modified secrets.
git add -A
git diff --cached    # Review what will be commited.
git commit
git push

# Commit and push the changes to datacoves.
cd ../..
git add -A
git diff --cached
git commit
git push
```

## Apply the release to a cluster

### Localhost

```bash
./cli.py install
```

### JNJ

For jnj there's a git repository, datacoves_deployment, that mirrors the structure of
the datacoves repo but only contains scripts and configuration, not sources.

To deploy first update the mirror:

```bash
# Clone if needed.
mkdir -p ../jnj/asx-ahrx/datacoves_deployment
git clone ssh://git@sourcecode.jnj.com:3268/asx-ahrx/datacoves_deployment.git ../jnj/asx-ahrx/datacoves_deployment

# Rsync the installer files into the datacoves_deployment repo
./cli.py rsync_installer ../jnj/asx-ahrx/datacoves_deployment/

# Point the config submodule to the latest version.
cd config/$cluster_domain/
git pull
cd ../..

# Commit the changes.
git add -A
git diff --cached
git commit
```

SSH into a jnj machine with kubectl access to the cluster. Then follow
[datacoves_deployment](https://sourcecode.jnj.com/projects/ASX-AHRX/repos/datacoves_deployment/browse)'s
[documentation](../client-docs/jnj/5-deployment.md) to run the installation scripts.

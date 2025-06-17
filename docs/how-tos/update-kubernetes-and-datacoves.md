# Statement of Purpose

The purpose of this document is to describe common upgrade procedures for both updating Kubernetes and updating Datacoves on customer clusters.


# Updating Kubernetes

The procedure varies for Azure vs. AWS.  We generally prefer to use the web console to do the upgrade.

## Gain Kubernetes command line access to the cluster

Make sure you are set up for Kubernetes command line access.

 * For Orrum the instructions are here: https://github.com/datacoves/datacoves/tree/main/docs/client-docs/orrum

Access whatever VPN is necessary.  Switch to the correct Kubernetes context:

```
kubectl config get-contexts
kubectl config use-context context-name
```

If you aren't set up to do this, stop now and get help.

## Disable Sentry Alarms

Sentry is going to complain very loudly about all this.

Currently, it looks like there is no way to disable this without the Sentry Business Plan which we do not have.  But if that ever changes, we'll update this section.  *For now, there is nothing to do.*

## Check and Prepare PDB's

The Kubernetes PDBs can cause an upgrade to hang, as it will prevent a pod from shutting down to receive the update.  Check the PDBs like this:

```
kubectl get pdb -A
```

You will get an output similar to:

```
NAMESPACE       NAME                           MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE
calico-system   calico-typha                   N/A             1                 1                     273d
core            api                            1               N/A               0                     232d
core            beat                           1               N/A               0                     232d
core            redis                          1               N/A               0                     232d
core            workbench                      1               N/A               0                     232d
core            worker                         1               N/A               0                     232d
dcw-dev123      dev123-airflow-scheduler-pdb   N/A             1                 1                     26h
dcw-dev123      dev123-airflow-webserver-pdb   N/A             1                 1                     26h
kube-system     coredns-pdb                    1               N/A               1                     273d
kube-system     konnectivity-agent             1               N/A               1                     273d
kube-system     metrics-server-pdb             1               N/A               1                     273d
```

Note the core namespace clusters with ALLOWED DISRUPTIONS at 0.  You will need to patch those so that they will allow a disruption, and then revert the patch when done.

The following commands will allow for a disruption:

```
kubectl patch pdb -n core api -p '{"spec":{"minAvailable":0}}'
kubectl patch pdb -n core beat -p '{"spec":{"minAvailable":0}}'
kubectl patch pdb -n core redis -p '{"spec":{"minAvailable":0}}'
kubectl patch pdb -n core workbench -p '{"spec":{"minAvailable":0}}'
kubectl patch pdb -n core worker-long -p '{"spec":{"minAvailable":0}}'
kubectl patch pdb -n core worker-main -p '{"spec":{"minAvailable":0}}'
kubectl patch pdb -n core dbt-api -p '{"spec":{"minAvailable":0}}'
kubectl patch pdb -n prometheus cortex-tenant -p '{"spec":{"minAvailable":0}}'
```

You can apply this to any other PDBs that prevent disruptions.  *Take note of all the PDBs that you altered in this fashion.*

## Upgrade Kubernetes

This varies based on the cloud provider.

### On Azure

Go to:

https://portal.azure.com/#view/HubsExtension/BrowseResource/resourceType/Microsoft.ContainerService%2FmanagedClusters

Make sure you are logged into the correct client account (check the upper right corner).

Locate the cluster you want to work with.  Often you will have to alter the default filters so that "Subscription equals all".

Pick the cluster you are updating.  If you are not sure which one, ask.

On the overview screen that comes up by default, you will see "Kubernetes version" in the upper right area.  Click the version number.

It will show version details; click Upgrade Version.

 * Pick Automatic upgrade: Enabled with patch (recommended)
 * Pick Kubernetes version: the version you wish to upgrade to
 * Pick upgrade scope: Upgrade control plane + all node pools
 * Click save

The upgrade will start in a few moments.

## Wait for it to come back

The update can take quite awhile.  Keep an eye on the pods and watch them update:

```
kubectl get pods -A
```

You will see a lot of activity, pods shutting down and restarting.  Once it's all back online, you can restore the PDBs (see next step) and you can verify the update (see bottom of this file).

## Restore PDB's

We need to put the PDB's back in place.

```
kubectl get pdb -A
```

You will get an output similar to:

```
NAMESPACE       NAME                           MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE
calico-system   calico-typha                   N/A             1                 1                     273d
core            api                            0               N/A               1                     232d
core            beat                           0               N/A               1                     232d
core            redis                          0               N/A               1                     232d
core            workbench                      0               N/A               1                     232d
core            worker                         0               N/A               1                     232d
dcw-dev123      dev123-airflow-scheduler-pdb   N/A             1                 1                     26h
dcw-dev123      dev123-airflow-webserver-pdb   N/A             1                 1                     26h
kube-system     coredns-pdb                    1               N/A               1                     273d
kube-system     konnectivity-agent             1               N/A               1                     273d
kube-system     metrics-server-pdb             1               N/A               1                     273d
```

The following commands will re-enable the PDBs:

```
kubectl patch pdb -n core api -p '{"spec":{"minAvailable":1}}'
kubectl patch pdb -n core beat -p '{"spec":{"minAvailable":1}}'
kubectl patch pdb -n core redis -p '{"spec":{"minAvailable":1}}'
kubectl patch pdb -n core workbench -p '{"spec":{"minAvailable":1}}'
kubectl patch pdb -n core worker-main -p '{"spec":{"minAvailable":1}}'
kubectl patch pdb -n core worker-long -p '{"spec":{"minAvailable":1}}'
kubectl patch pdb -n core dbt-api -p '{"spec":{"minAvailable":1}}'
kubectl patch pdb -n prometheus cortex-tenant -p '{"spec":{"minAvailable":1}}'
```

Also restore any additional PDBs you had to disable in the prior step.

# Updating DataCoves

Updating DataCoves is relatively simple.  However, some of the access details can be compllicated.

## First Time Setup: Set Up Deployment Environment and Get Needed Access

J&J, Kenvue, and Orrum have some complexity around access.  AKS access is relatively easy.  These are one-time steps you need to take to get access to each environment.

### AKS

Accessing AKS is documented here: https://github.com/datacoves/datacoves/blob/main/docs/how-tos/administrate-east-us-a-aks-cluster.md

Installation is done using your development system's checked out copy of the Datacoves repository.  AKS' configuration repository is located at: https://github.com/datacoves/config-datacoves-east-us-a and should be checked out into your 'config' directory.

### Orrum

Accessing Orrum is documented here: https://github.com/datacoves/datacoves/tree/main/docs/client-docs/orrum

Installation is done using your development system's checked out copy of the Datacoves repository.  Note that Orrum requires a VPN, but the access is described above.  Orrum's configuration repository is here: https://github.com/datacoves/config-datacoves-orrum and must be checked out into your 'config' directory.

### CCS

To access CCS, your Datacoves account must be added to CCS' Azure organization.  Eugine Kim can assist with this.

Then, you must download and install the Azure VPN client.  For Macs, this is done through the Apple Store.

And finally, you need the Azure command line tools which you probably already have installed if you followed our README instructions for setting up this repository.  You should also be logged into Azure with `az login`.

Then, on the VPN, you can shell into the Bastion as follows:

```
az ssh vm --subscription 3099b8af-7ca1-4ff4-b9c5-1960d75beac7 ssh vm --ip 10.0.2.4
```

Once on the Bastion, the tools are installed with Linux Brew:  So, edit your `.bashrc` file in your home directory with your favorite editor and add this to the end:

```
eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
```

Log out and log back in.  ```python3 --version``` should reveal a modern `3.1x` python version.


From this point, it is simply check out the datacoves repository and do the installation like any other system.

### J&J / Kenvue

J&J access is complex; going into the details of all the setup is out of the scope of this documentation.  However, we will cover how to get set up on the bastion so you can get to work.

It is a good idea to read this documentation if you haven't already: https://github.com/datacoves/datacoves/tree/main/docs/client-docs/jnj

In order to do deployments in J&J or Kenvue, you have to do the work from a bastion server, which is a Linux machine accessible via your Cloud PC.  J&J and Kenvue have different bastions, however configuring them is basically the same.

The IP address for the J&J Bastion is: `10.157.82.138` and the IP address for the Kenvue bastion is: (... I am unable to log into Kenvue right now! Great!)

I make a `.bat` file that runs `ssh IP` where the IP is the one above.

Once you log into the bastion, there's a few things to note:

 - You can sudo to root thusly: `sudo su -`.  Any other `sudo` command will not work, you can only `sudo su -`.
 - The default home directory you log into on the bastion does not have much disk space, so we use a volume mount on `/app` for most of our work.
 - We use `brew` to manage packages.

To get set up initially, take the following steps:

#### Copy base configuration

```cp -R /app/users/datacoves-home-template/. ~/```

#### Add brew to your bash rc

Edit your `.bashrc` file in your home directory with your favorite editor and add this to the end:

```
eval $(/home/linuxbrew/.linuxbrew/bin/brew shellenv)
```

Log out and log back in.  ```python3 --version``` should reveal a modern `3.1x` python version.

#### Login to Kubernetes

```
kubectl config get-contexts
```

#### Set up your deployment repository

```
sudo su -
mkdir -p /app/users/$USER
chown -R $USER /app/users/$USER
exit
cd /app/users/$USER
git clone https://github.com/datacoves/datacoves.git
cd datacoves
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

#### Set up your configuration repository

For each environment you will deploy to, you need to check out its config repository into your 'configs' directory.  The list of repositories is here:

https://github.com/datacoves/datacoves/blob/main/docs/client-docs/jnj/1-cluster-requirements.md

## Before Deployment: Create your Plan

Before a deployment is done, you must first check to see if there's any special installation steps.  I use a Word document template, and I update it according to each release adding any special steps that I need to.  Then I print it out and use it as a physical check list.  My template file is [here](DeploymentTemplate.doc).

First, look at the version of the cluster you will be updating.  You can get this version from the cluster-params.yaml.  The easiest way to do this is to check the difference between two versions in GitHub.  Here's an example of a comparison between two versions:

https://github.com/datacoves/datacoves/compare/v3.2.202410250048...v3.2.202411140044

Look at all the pull requests that are in your new releae and check to see if you have any that are labeled "special release step" and add any special steps to your release document.  Post your finished work on the Slack dev channel for commentary.

## Perform the installation

Release documentation is here: https://www.notion.so/datacoves/Release-Instructions-1b5ea827f87280f98620dccc1600727c  **Be very sure you are releasing from the correct release branch**.  You need to release from the tag you are releasing.  You can check out a tag thusly:

```
git fetch -a
git checkout refs/tags/v1.2.34234523452524
```

Replace the tag name with the version you are deploying.  If you deploy from main or the wrong branch, you risk using installation scripts that are newer and have features that aren't supported yet by the images you are edeploying.

### How to run migrations on a stuck install process

Sometimes migrations do not run automatically because the new pod containing the migrations fails before they can be applied. When this occurs we need to execute them manually. So we need to remove the `LivenessProbe` and `ReadinessProbe`, this makes the new pod run correctly and allows us to enter it and execute the migrations ourselves.

```shell
kubectl patch deployments -n core api -p '{"spec": {"template": {"spec": {"containers":[{"name": "api", "livenessProbe": null, "readinessProbe": null}]}}}}'
```

When the pod run correctly.

```shell
kubectl -n core get pods
kubectl -n core exec -it api-<hash> -- bash
./manage.py migrate
```

### Create Profile Image Set for New Release

This may be necessary if an error about Profile Image Sets occurs; it is a bit of a chicken and the egg problem, as the release needs to exist prior to creating the profile image set, but the release won't exist until the install process is attempted.

Log into the customer's API panel.

 * Orrum's is: https://api.datacoves.orrum.com/panel
 * CCS' is: https://api.datacoves.cssperfusion.com/panel

Under "Projects" pick "Profile Image Sets".  Go to the existing Profile Image Set for the old release, and copy / paste the 4 JSON blocks into an editor.  Take a note of what is in the 'profile' field.

Go back to the listing of Profile Image Sets and click `+ Add profile image set` in the corner.  Make the profile the same as the previous release's, and choose the new release from the release select box.

Then, paste in the four JSON blocks into the new Profile Image Set.  Check your release YAML file in `releases` and note the section 'code_server_libraries'; compare that to the Python libraries in the profile image set.  Update versions as needed, but never downgrade.  There's no need to add libraries that are in the release YAML but not in the profile image entry.

Also check 'code_server_extensions' against 'code server extensions' and apply the same logic to update extensions that are in the Profile Image Set.

Save the new profile image set, and making sure to keep all the data from the old profile image set just in case you need it, go back into that one and delete it.

You can now re-run installation and it should get past this error.

# Verify Installation

Verifying the installation is the same no matter what process you're engaging in with DataCoves clusters, be it a Kubernetes update or a DataCoves update.

 * Make sure no helm chart failed and retry if needed: `./cli.py retry_helm_charts`
 * Log into the customer's API panel and make sure that is working.
 * Log into the customer's launchpad and make sure that is working.
 * Pick one of the customer's environments and make sure you can get into it.
   * Try to use code server ("Transform")
   * Open a terminal in code server and run `dbt-coves --version`
   * Try to use Airflow ("Orchestrate")
   * Look at logs in one of the DAGs

If your user does not have permission to get into the customer's cluster, temporarily add yourself to the necessary groups to check the cluster.

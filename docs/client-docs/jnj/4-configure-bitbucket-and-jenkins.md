# How to configure Bitbucket project and connect it with Jenkins project

## Bitbucket

### Ensure you enable the following hooks in your Bitbucket project

- JnJ VPCx - Post Receive Repository Hook for SCM
- Webhook to Jenkins for Bitbucket Server

![Bitbucket hooks](img/bitbucket-project-settings-hooks.png)

### JnJ VPCx - Post Receive Repository Hook for SCM

![Post Receive Repository Hook for SCM](img/bitbucket-project-settings-post-receive-repository-hook.png)

### Webhook to Jenkins for Bitbucket Server

#### Tab 1

![Webhook tab 1](img/bitbucket-project-settings-jenkins-webhook-tab1.png)

#### Tab 2

![Webhook tab 2](img/bitbucket-project-settings-jenkins-webhook-tab2.png)

#### Tab 3

![Webhook tab 3](img/bitbucket-project-settings-jenkins-webhook-tab3.png)

### Enable the following Merge Checks

![Merge Checks](img/bitbucket-project-settings-merge-checks.png)

### Request access to taqy-docker for the project service account

Typically the service account created automatically is `sa-itsus-<PROJECT CODE>-devusr`.

Go to App Dev Tools and request access for that user, like so:

![App Dev Tools](img/app-dev-tools-artifactory-sa.png)

## Jenkins

### Ensure Bitbucket plugins were correctly configured

Navigate to Manage Jenkins -> Configure System and modify the following plugins:

![Bitbucket Server](img/jenkins-configuration-bitbucket-server.png)

![Bitbucket Notifier](img/jenkins-configuration-bitbucket-notifier.png)

### Create Multibranch pipeline project

At Home page -> "+ New Item":

![Multibranch pipeline project](img/jenkins-create-multi-branch-pipeline.png)

### Configure branch sources

![Branch sources](img/jenkins-settings-branch-sources.png)

### Configure repo behaviors

![Branch repo behaviors](img/jenkins-settings-behaviors.png)

### Set up build configuration and other items

![Build configuration](img/jenkins-settings-build-configuration.png)

![Other items](img/jenkins-settings-other.png)

## Jenkinsfile dependencies

You'll need a credential that stores the secrets used to connect to your Data Warehouse.

Create a new credential in the Jenkins Admin area. As of Aug. '23 those can be found in:

`Dashboard -> Credentials -> System -> Global Credentials (unrestricted)`

![New credential](img/jenkins-add-new-credential-0.png)

![New credential](img/jenkins-add-new-credential.png)


## Known issues


* When "pre hook declined" it could be due to JIRA issues configuration: from settings -> `Jira Issues` select "Use custom settings" and  be sure "Don't need a Jira issue key" is selected
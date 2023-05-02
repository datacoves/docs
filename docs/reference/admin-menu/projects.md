# Projects Admin

## Overview

A Project is the highest grouping in Datacoves. It is what contains environments, which then are linked to services, connections, etc.

The Datacoves landing page (Launch Pad) follows this hierarchy:

![Project Environment Difference](./assets/launchpad_environments_projects.png)

## Projects Listing

![Projects Listing](./assets/projects_landing.png)

On the Projects landing page you can see a list of projects associated with your Datacoves account.

For each project, you will see number of defined connection templates and environments. You will also see the status of the git connection(tested or not).

Each row contains 3 action buttons, Test, Edit and Delete.

### Testing connection

Testing your repo connection ensures that services like dbt docs and Orchestration are available. It is important to test the connection to git to make sure the system can clone your repository. If the test fails, this indicates that Datacoves cannot clone your repository this will affect serving production dbt docs and Airflow jobs. Edit your environment and check your settings then click the test button again to assure the git status is "Tested".

## Create/Edit Project

![Projects Create or Edit Page](./assets/projects_editnew_page.png)

A Project configuration consists of the following fields:
- **Name** This is what will be displayed in the Datacoves landing page.
- **Git Repo** This is the git repository associated with this project
    - **Clone strategy** determines how Datacoves will communicate with your git repository(SSH or HTTPS). Each clone strategy is configured as follows:
        - **SSH** When SSH is selected, an SSH public Key will be automatically generated for you to configure in your git provider as a deployment key.
        ![Repo SSH Key](./assets/projects_ssh_key.png)
        - **HTTPS** When HTTPS is selected, the following fields must be filled in `Git HTTPS url`, `Username` and `Password`
        ![Repo User Password Prompt](./assets/projects_https_data.png)
    - **Release branch** defines the default branch in your repository. This is typically `main` or `master`
- **CI/CD Provider** when provided, this will display a link to your CI/CD jobs on the Observe tab of a Datacoves environment. Once you choose your provider, you will be able to specify your `CI jobs home url`

# How to Create/Edit a Project
Navigate to the Projects page

![Projects Page](./assets/menu_projects.gif)

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

# Groups Admin

## Overview

A Group in Datacoves is a collection of permissions, which can be assigned to your account's users.
By default, one group comes shipped with your account, the `Account Admin`. Also, when you create a [Project](/reference/admin-menu/projects.md) or an [Environment](/reference/admin-menu/environments.md), two groups are created for each of them: `Project/Environment Developer` and `Project/Environment Viewer`

| Group type | Group Name | Default Privileges |
|------------|------------|--------------------|
| Admin | Account Admin | Manages billing, and the rest of the options within the admin menu |
| Project Developer | _\<Account Name\> \<Project Name\>_ Project Developer | Can access all environments within the given project. Developers get access to the IDE |
| Project Viewer | _\<Account Name\> \<Project Name\>_ Project Viewer | Can access dbt docs in all environments |
| Environment Developer | _\<Environment Name\> (\<Environment Slug\>)_ Environment Developer | Can access only the specific environment. Developers get access to the IDE |
| Environment Viewer | _\<Account Name\> \<Project Name\>_ Project Viewer | Can see dbt docs only in the specific environment. |


## Groups Listing

![Groups Listing](./assets/groups_listing.png)

On the Groups landing page you can see your account's list of groups

For each group we can see it's name, the number of permissions it has enabled, and how many users are using it.

Each row contains 2 action buttons, Edit and Delete.
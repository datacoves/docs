# Groups Admin

## Overview

A Group in Datacoves is a collection of permissions, which can be assigned to your account's users.
By default, one default group exists for your account, the `Account Admin`. When you create a [Project](/reference/admin-menu/projects.md), three groups are created: `Project Developer`, `Project Sys Admin` and `Project Viewer` Additionally, when an [Environment](/reference/admin-menu/environments.md) is created, three additional groups are created for each environment: `Environment Developer`, `Environment Sys Admin` and `Environment Viewer`.

>[!TIP]See our How To - [Groups](how-tos/datacoves/how_to_groups.md) for information on editing group permissions and associating groups with AD groups for Datacoves enterprise installations.

| Group type           | Group Name                                            | Default Privileges                                                                                                 |
|----------------------|-------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| Admin                | Account Admin                                         | Manages billing, and other administrative tasks such as managing users, creating environments, and service connections.                                                 |
|||||
| **Project** Developer | _\<Account Name\> \<Project Name\>_ Project Developer | Can access all environments within the given project. Gets an individual VS Code IDE for each environment. Developers can also create and modify Superset objects. |                                                                         |
| **Project** Sys Admin | _\<Account Name\> \<Project Name\>_ Project Sys Admin | Can access Superset, data sources, and has Airflow admin capabilities in all environments within the given project. |
| **Project** Viewer | _\<Account Name\> \<Project Name\>_ Project Viewer    | Can access dbt docs in all environments   |
|||||
| **Environment** Developer| _\<Environment Name\> (\<Environment Slug\>)_ Environment Developer | Can access only the specific environment. Gets an individual VS Code IDE for the specific environment. Developers can also create and modify Superset objects in the specific environment. |
| **Environment** Sys Admin| _\<Environment Name\> (\<Environment Slug\>)_ Environment Sys Admin | Can access Superset data sources and has Airflow admin capabilities in the specific environment.                  |
| **Environment** Viewer   | _\<Account Name\> \<Project Name\>_ Environment Viewer| Can see dbt docs only in the specific environment. |

## Groups Listing

![Groups Listing](./assets/groups_listing.gif)

On the Groups landing page you can see your account's list of groups

For each group we can see the group's name, the number of permissions it has, and how many users are assigned to it.

Each row contains 2 action buttons, Edit and Delete.
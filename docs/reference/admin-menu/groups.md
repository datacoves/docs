# Groups Admin

## Overview

A Group in Datacoves is a collection of permissions, which can be assigned to your account's users.
By default, one default group exists for your account, the `Account Admin`. 

When you create a [Project](/reference/admin-menu/projects.md), four groups are created:
- `Project Admin`
- `Project Developer`
- `Project Sys Admin`
- `Project Viewer` 

Additionally, when an [Environment](/reference/admin-menu/environments.md) is created, four additional groups are created for each environment: 
- `Environment Admin`
- `Environment Developer`
- `Environment Sys Admin`
- `Environment Viewer`

>[!TIP]See our How To - [Groups](how-tos/datacoves/how_to_groups.md) for information on editing group permissions and associating groups with AD groups for Datacoves enterprise installations.

### **User Groups & Default Privileges in Datacoves**

| **Group Type**              | **Group Name**                                          | **Default Privileges**                                                                                         |
|----------------------------|--------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **Admin**                  | Datacoves Admin                                        | Manages **billing, Grafana, platform-wide settings**, and other administrative tasks such as managing users, creating environments, and service connections. |
| **Project Admin**          | _\<Account Name\> \<Project Name\>_ Project Admin     | Has **full control** over project-level settings, including enabling tools. Has access to **Airflow Variables and Connections**. Can create **DataHub integrations**. Can access all tools under each environment in the project. Can manage **Grafana dashboards**. |
| **Project Developer**      | _\<Account Name\> \<Project Name\>_ Project Developer | Can access all environments within the project. Gets an individual **VS Code IDE** for each Development environment. Can create and modify **Superset objects**. Has **editor access in DataHub**. Can **use Airbyte**. Has viewer access in **Grafana**. |
| **Project Sys Admin**      | _\<Account Name\> \<Project Name\>_ Project Sys Admin | Can access all environments within the project. Can access **Superset and DataHub data sources**. Can **see the Airflow Admin menu**, **create Airflow connections**, and **trigger DAGs**, but **cannot access or add Airflow Variables**. Has **editor access in DataHub**. Can **use Airbyte**. Has viewer access in **Grafana**. Can create and modify **Superset objects**. |
| **Project Viewer**         | _\<Account Name\> \<Project Name\>_ Project Viewer    | Can access all environments within the project. Can view **dbt docs in all environments**. Has viewer access to **airflow**, **datahub**, **superset** and **grafana**. |
| **Environment Admin**      | _\<Environment Name\> (\<Environment Slug\>)_ Environment Admin | Has **admin rights** for the environment and enabled tools. Has **Airflow Admin rights**, can **extract Airflow variables**, create **DataHub integrations**, and configure **Superset security settings**. Can manage **Grafana** dashboards. |
| **Environment Developer**  | _\<Environment Name\> (\<Environment Slug\>)_ Environment Developer | Can access only the specific environment. Gets an individual **VS Code IDE** for the environment. Can create and modify **Superset objects**. Has **editor access in DataHub**. Can **use Airbyte**.  Has viewer access in **Grafana**. |
| **Environment Sys Admin**  | _\<Environment Name\> (\<Environment Slug\>)_ Environment Sys Admin | Can access **Superset and DataHub data sources**. Can **see the Airflow Admin menu**, **create Airflow connections**, and **trigger DAGs**, but **cannot access or add Airflow Variables** (must be added by someone else for security). Has **editor access in DataHub**. Can **use Airbyte**. Has viewer access in **Grafana**.  Can create and modify **Superset objects**. |
| **Environment Viewer**     | _\<Account Name\> \<Project Name\>_ Environment Viewer | Can view **dbt docs only in the specific environment**. Has viewer access to **airflow**, **datahub**, **superset** and **grafana**. |

---

### **Tool-Specific Group Requirements**

| **Tool**      | **Required Roles** |
|--------------|-------------------|
| **Airbyte** | Must have **Admin, Sys Admin, or Developer** to use Airbyte. |
| **Team Airflow** | Must have **Environment Admin or Project Admin** to extract variables. **Sys Admins** can see the **Admin menu** and create connections but **cannot access or add variables**. **Sys Admins & Developers** can trigger DAGs. |
| **My Airflow** | Must have **Environment Developer or Project Developer** and **Environment Sysadmin or Project Sysadmin** to access My Airflow. |
| **DataHub** | Must have **Environment Admin or Project Admin** to create integrations. **Developers and Sys Admins** have **editor access in DataHub**. |
| **dbt Docs** | Must have **Production Environment Developer or Viewer** to view **dbt docs** in production. **Developers** can run **local dbt-docs**. |
| **Superset** | Must have **Environment Admin or Project Admin** to modify security settings. Developers can create and modify **Superset objects**. |

## Groups Listing

![Groups Listing](./assets/groups_listing.gif)

On the Groups landing page you can see your account's list of groups

For each group we can see the group's name, the number of permissions it has, and how many users are assigned to it.

Each row contains 2 action buttons, Edit and Delete.
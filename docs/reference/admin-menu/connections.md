# Connections Menu

## Concept

<!-- TODO: Get a proper well-writen concept of what a Connection in Datacoves is -->
A Connection in Datacoves is the definition of basic information of your data warehouse provider(s). It acts as a template that then [Service Connections](/reference/admin-menu/service_connection.md) will complete and use to connect to your services.

## Landing

![Connections Menu Landing](./assets/connections_landing.png)

In the landing page of Connections' Menu, you can see a list of Connections linked to your [projects](/reference/admin-menu/projects.md). In each of them, the provider (i.e. Snowflake), and the amount of services and users that are using it. Each also present the possibility of being edited or deleted.

## Create/Edit Connection

![Connections Create or Edit Page](./assets/connections_editnew_page.png)

Each Connection consist of the following information:
- Name
- Enabled for users: states whether this Connection is usable by other users when creating their DB connections.
- Project: Datacoves' [Project](/reference/admin-menu/projects.md) to link to.
- Type: data warhouse provider.
- Default values: provider connection details. It will vary depending on `type` selection:
    - When selecting `Snowflake`: `Account`, `Warehouse`, `Database`, `Role` must be set.
    ![Snowflake Connection Type](./assets/connections_editnew_snowflake.png)
    - When using `Redshift`, you use `Host` and `Database` instead.
    ![Redshift Connection Type](./assets/connections_editnew_redshift.png)

# Service Connections Menu

## Concept

<!-- TODO: Get a proper well-writen concept of what a Project in Datacoves is -->
While Connections act as templates for connecting to a data warehouse provider, Service Connections are the ones that leverage the connection itself. They are the ones that create the connection for a user or a service account, by grabbing a Connection, adding the final connection details (authentication) and linking it to an Environment

## Landing

![Service Connections Menu Landing](./assets/serviceconnection_landing.png)

In the landing page of Service Connections' Menu, you can see a list of Service Connections linked to your Environment(s). In each of them, the service it connects and the type of Connection it connects to.

Apart from the standard Edit and Delete actions, these SC can be tested and, more importantly, give you hints on how to use the Connections it'll create in your Environments.

## Create/Edit Service Connection

![Service Connection Create or Edit Page](./assets/serviceconnection_editnew_page.png)

Each Service Connection consist of the following fields:
- Name
- [Environment](/reference/admin-menu/environments.md)
- Service
- [Connection](/reference/admin-menu/connections.md): once selected, the Connection will expand it's templated information (fields that you can override by toggling their respective sliders), and you'll have to complete the missing ones.

![Service Connection Connection Details](./assets/serviceconnection_editnew_details.png)

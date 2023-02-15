# Integrations Menu

## Concept

<!-- TODO: Get a proper well-writen concept of what a Project in Datacoves is -->
Integrations are the mechanism used to inject extra information inside your Environment, data that is provided via environment variables and linked to services. We currently support 2 types of integrations:
- SMTP: used to [send email notifications from Airflow](/how-tos/airflow/send-emails.md)
- MS Teams: used to [send Microsoft Teams messages from Airflow](/how-tos/airflow/send-ms-teams-notifications.md)

## Landing

![Integrations Menu Landing](./assets/integration_landing.png)

Integration's landing page is straight forward: it shows each Integration with it's name and type.

## Create/Edit Integration

![Integration Create or Edit Page](./assets/integration_editnew_page.png)

Each Integration consist of the following:
- Name
- Type: we currently support only `SMTP` and `MS Teams` types. Depending on your selection, different configuration fields will show up, which we've already covered in their own Docs section:
    - SMTP -> [send email notifications from Airflow](/how-tos/airflow/send-emails.md)
    - MS Teams -> [send Microsoft Teams messages from Airflow](/how-tos/airflow/send-ms-teams-notifications.md)

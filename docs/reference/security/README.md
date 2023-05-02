# Datacoves Security

Security and Privacy are fundamental pillars in Datacoves.

We are committed to keeping your data safe by following industry-leading standards for securing physical deployments, setting access policies, managing our network, and setting policies across our organization.

## Authentication

Datacoves allows users to log in to the platform via Single Sign On(SSO) using your organization's Google or Microsoft account(contact support).

## Access Control

Datacoves supports user management and role-based access control (RBAC).

## Communication & Encryption

- Any HTTP connection attempt is forwarded to HTTPS.

- We employ HSTS to guarantee that browsers only communicate with Datacoves over HTTPS.

- All connections to Datacoves are by default encrypted, using contemporary ciphers and cryptographic techniques, in both directions.

- For all data that is encrypted at rest, we use AES-128.

## Data Processing

### IDE

The data from your database will traverse the Datacoves infrastructure on the way to your browser when you write interactive queries from the IDE. But this information is not preserved in any way (caching or otherwise). Outside of your browser sessions, it does not reside on our servers.

### Airbyte Service

Airbyte connectors operate as the data pipes moving data from Point A to point B: Extracting data from data sources (APIs, files, databases) and loading it into destination platforms (warehouses, data lakes) with optional transformation performed at the data destination. As soon as data is transferred from the source to the destination, it is purged from your Datacoves environment.

Environments with Airbyte installed store the following data:

#### Technical Logs

Technical logs are stored for troubleshooting purposes and may contain sensitive data based on the connection’s state data. If your connection is set to an Incremental sync mode, users choose which column is the cursor for their connection. While we strongly recommend a timestamp like an updated_at column, users can choose any column they want to be the cursor.

#### Configuration Metadata

Datacoves retains configuration details and data points such as table and column names for each integration.

#### Sensitive Data​

As Datacoves is not aware of the data being transferred, users are required to follow the Terms of Service and are ultimately responsible for ensuring their data transfer is compliant with their jurisdiction.

## Data Storage

Datacoves stores the following data persistently:

- Datacoves account details, such as job definitions, database connection details, user information, etc. Raw data from your warehouse is not included in cloud account information.
- Logs associated with jobs and interactive queries you’ve run.

Unless the code you write creates it, the warehouse's data is not included in logs or assets. For instance, you could create code that reads every piece of customer information from your customer table and logs it. Although it's generally not a good idea to do that, it is conceivable and would imply that data is stored in Datacoves.

## Availability, Business Continuity, & Disaster Recovery

Datacoves is hosted in Azure and Amazon Web Services, with availability in multiple AZ’s (availability zones) in a region.

We save backups for at least seven (7) days.

Our employees are dispersed remotely across the US and Latin America and we offer service to consumers everywhere. We can practically give help from anywhere thanks to our distributed staff, which also lessens the effects of support interruptions in certain geographic areas.

## Security Protocols

Datacoves data centers are hosted using Azure and Amazon Web Services, where they are protected by electronic security, intrusion detection systems, and 24/7/365 human staff.

Datacoves runs operating systems that are actively maintained, long-term supported, and patched with the most recent security updates.

We only allow a few senior personnel access to sensitive information.

Before deploying a platform release, we examine new features for any security risks.

## Security Recommendations

Ensure that only the datasets processed by Airbyte, dbt, Airflow, or Superset are given access to your warehouse by Datacoves.

To protect your data and login credentials while in transit, use SSL or SSH encryption. For users in your database, pick secure passwords or use key-based authentication when possible.

## Contact us

To stay current with the most recent security methods, Datacoves is dedicated to collaborating with security professionals throughout the world. We kindly request that you notify us immediately if you discover any security flaws in Datacoves.

Please email us at support@datacoves.com if you think you have found an issue or if you have any queries.

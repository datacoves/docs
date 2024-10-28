# Configure your account with Datacoves

>[!ATTENTION]The appropriate git repo access is required to be able to add deployment keys, be sure that you can add ssh keys to the repo or we will not be able to finish setup.

## Prerequisites

Before the setup call with the Datacoves team, ensure you have the following ready.

>[!NOTE]Email gomezn@datacoves.com and mayra@datacoves.com with the answers to the following two questions so we can be ready for the call.

1. What version of dbt are you using?
2. Do you use Google / Google Workspace or Microsoft to authenticate? Datacoves leverages your existing authentication service.

### Data Warehouse

To set up your Datacoves account, you will need to know your data warehouse provider and have relevant access details handy. This includes the service account that Airflow will use.  
        
| Data Warehouse Provider | Information Needed |
| --- | --- |
| Snowflake | Account, Warehouse, Database, Role, User, Password, Schema |
| Redshift | Host, Database, User, Schema, Password |
| Databricks | Host, Schema, HTTP Path, Token |
| BigQuery | Dataset, Keyfile JSON |

>[!WARNING] For the Snowflake `Account` field you will need to find your account locator and replace `.` with `-`. Check out [Snowflake Fields](how-tos/datacoves/how_to_connection_template.md#for-snowflake-the-available-fields-are) on how to find your Snowflake account locator.

**Network Access:** Verify that your Data Warehouse is accessible from outside your network. You'll need to whitelist the Datacoves IP - `74.179.200.137`

### Git

To configure the git integration, you will need:

**Git Access** Ensure your user has access to add a deployment key to the repo, as well as access to clone and push changes.

**Git Repo** If this will be a new dbt project, create a new repo and ensure at least one file is in the `main` branch such as a `README.md`. Have your git clone URL handy.

**dbt Docs** Create a `dbt-docs` branch in your repo.

## During Call with Datacoves
To ensure a smooth call, please have the answers to the following questions ready to go. 

- What do you want to call your account? (This is usually the company name)
- What do you want to call your project? (This can be something like Marketing DW, Finance 360, etc)
- Do you currently have a CI/CD process and associated script like GitHub Actions workflow? If not, do you plan on creating a CI/CD process?
- Do you need any specific python library on Airflow or VS Code? (outside the standard dbt related items)


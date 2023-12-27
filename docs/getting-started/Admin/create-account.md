# Configure your account with Datacoves

## Prerequisites

Before the setup call with the Datacoves team, ensure you have the following ready.

?> Email ngomez3@datacoves.com and mayra@datacoves.com with the answers to the following 2 questions so we can be ready for the call.
1. What version of dbt are you using?
2. What type of account are you using to authenticate? ie) Google or Microsoft 

### Data Warehouse

**Warehouse Details** Know your data warehouse provider and have relevant access details handy. This includes the service account that Airflow will use.  
        
| Data Warehouse Provider | Information Needed |
| --- | --- |
| Snowflake | Account, Warehouse, Database, Role, User, Password, Schema |
| Redshift | Host, Database, User, Schema, Password |
| Databricks | Host, Schema, HTTP Path, Token |
| BigQuery | Dataset, Keyfile JSON |


**Network Access:** Verify if your Data Warehouse is accessible from outside your network. You'll need to whitelist the Datacoves IP - `40.76.152.251`

### Git

**Git Access** Ensure your user has access to add a deploypment key to the repo, as well as clone access.

**Git Repo** If it is a new project, create a new repo and ensure at least one file is in the main branch such as a `README.md`. Have your git clone URL handy.

**dbt Docs** Create a `dbt-docs` branch in your repo.

## During Call with Datacoves
To ensure a smooth call, please have the answers to the following questions ready to go. 

- What do you want to call your account? (This is usually the company name)
- What do you want to call your project? (This can be something like Marketing DW, Finance 360, etc)
- Do you currently have a CI/CD process and associated script like GitHub Actions workflow? If not, do you plan on creating a CI/CD process?
- Do you need any specific python library on Airflow or VS code? (outside the standard dbt related items)


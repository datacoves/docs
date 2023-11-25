# Configure your account with Datacoves

## Prerequisites

Before diving into the setup call, ensure you have the following ready:

1. **Data Warehouse Details:** Know your data warehouse provider and have relevant access details handy. This includes the service account that Airflow will use.  
    
    
    | Data Warehouse Provider | Information Needed |
    | --- | --- |
    | Snowflake | Account, Warehouse, Database, Role, User, Password, Schema |
    | Redshift | Host, Database, User, Schema, Password |
    | Databricks | Host, Schema, HTTP Path, Token |
    | BigQuery | Dataset, Keyfile JSON |
2. **Git Access:** Ensure you have clone access with your Git provider such as GitHub or BitBucket.
3. **Git Repo** If it is a new project, create a new repo and ensure at least one file is in the main branch such as a README.md. Have your git clone URL handy.
4. **Network Access:** Verify if your Data Warehouse is accessible from outside your network. If not, you'll need to whitelist this specific IP - `40.76.152.251`
5. **dbt Docs** Create a `dbt-docs` branch in your repo.

## During Call with Datacoves
To ensure a smooth call, please have the answers to the following questions ready to go. 

- What do you want to call your account? (This is usually the company name)
- What do you want to call your project? 
- If using Airbyte, do you have any private API/db you need to access?
- Do you have CI? Are you going to develop the CI scripts? Do you have anything already?
- Do you need any specific python library on airflow or VS code? (outside the standard dbt stuff)




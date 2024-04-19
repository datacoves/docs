# Deploy your dbt Docs

## Local Docs 📖
1. Simply run `dbt docs generate` in your terminal 
   
![Docs Generate](assets/migration_docs_generate.png)

2. Click on the the Observe tab and view local docs
   
![Observe Tab](./assets/migration_observe_dbt_docs.png)

## Production dbt Docs 

Datacoves hosts your production docs and they are deployed via a CI/CD process with github actions. 

To configure this functionality:

**Step 1:** Head to your Environment Settings 

![Environment Menu](./assets/migration_environments.gif)

**Step 2:** Click `Stack Service` and turn on the `Observe > Local Docs Tab`. This will populate the `Docs settings` as seen below.

![Environment Observe Settings](./assets/migration_environment_observe_settings.gif)

Your designated docs branch has been set to `dbt-docs` for you. 
![dbt docs settings](./assets/migration_environment_dbt_docs.png)

**Step 3:** Create a branch in your repo named `dbt-docs`. 
>[!TIP]You can complete step 3 by heading into your project in the Datacoves UI(Click Open) > Click into the Transform Tab > Open a terminal > Type `git co -b dbt-docs` > Publish branch  

The service will not be available until you complete this step.

![Launchpad dbt docs](./assets/migration_launchpad_dbt_docs.png)

**Step 4:** 


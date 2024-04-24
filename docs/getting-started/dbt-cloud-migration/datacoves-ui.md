# Datacoves UI

## Launchpad
After you have completed the wizard, you will see your project in the launch pad. 

If some of your tools in the Launchpad are red this just means they need to be configured. You can hover over them to get helpful messages. However, by the end of this migration guide they should be all green as seen in the image below 🎉

Your **project** has been associated to your **repo** during the wizard setup as seen in the red box below.

![Migration Launch Pad](./assets/migration_launchpad.png)

All other environment settings have been configured for you during the setup Wizard step. 

## VSCode

1️⃣ Head into the `Transform` tab by selecting `Open` in the Launch pad. 

2️⃣ Click into the `Transform` tab to see VSCode. Your dbt development environment should be ready to go so let's take it for a spin.

3️⃣ You will be using the terminal to run dbt commands. Open a new terminal using Control + Shift + `  (tilde).

4️⃣ Enter `dbt debug` to ensure everything is running as expected.

5️⃣ Explore your models by opening one up and hitting `Command + Enter` to preview the data. 

6️⃣ Run a model of your choice by entering `dbt run -s <your_model>` in the terminal.

7️⃣ Verify the model populated in your warehouse using the Snowflake extension or by logging in to your data warehouse.

**To learn more about the dbt workflow in Datacoves see [dbt in Datacoves](getting-started/developer/working-with-dbt-datacoves.md)**

## Local Docs 📖
1️⃣ To view your local docs, simply run `dbt docs generate` in your terminal 
   
![Docs Generate](assets/migration_docs_generate.png)

2️⃣ Click on the the `Observe` tab and view local docs
   
![Observe Tab](./assets/migration_observe_dbt_docs.png)

## Next Steps

You are now ready to [configure Airflow](getting-started/dbt-cloud-migration/dbt-airflow-config.md)
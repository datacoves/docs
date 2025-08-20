# Using Key-Pair Authentication in Airflow

> [!NOTE] This documentation will presume you have knowledge of Datacoves' [Service Connections](/how-tos/datacoves/how_to_service_connections.md) and how to configure them.

First of all, using RSA Keys is only allowed through Airflow Connections, not Environment Variables. Make sure your Service Connection is using this `delivery mode`.

![alt text](assets/delivery_mode_airflow_connection.png)

Also, make sure to select `Authentication mechanism: RSA Key-pair` and [assign the generated key to your Snowflake user](https://docs.snowflake.com/en/user-guide/key-pair-auth#assign-the-public-key-to-a-snowflake-user).

![authentication_mechanism_copy](assets/authentication_mechanism_copy.png)

Once you have properly configured your Service Connection, your Airflow instance will restart (process that can take up to 10 minutes).

To confirm the above worked correctly, you can access your Airflow `Admin -> Connections` menu, and make sure your Service Connection  is now an Airflow Connection.

![airflow_admin_connections](assets/airflow_admin_connections.png)

## Usage

Thanks to our new [`dbt` Airflow Decorator](/reference/airflow/datacoves-decorators.md), you can run dbt against your warehouse using the Airflow Connection you just created, by simply passing the Service Connection name to our decorator's `connection_id` parameter.



```python
@dag(
    [...]
)
def dbt_dag():

    @task.datacoves_dbt(
        connection_id="main_key_pair" # your service connection name
    )
    def run_dbt():
        return "dbt debug" # return any dbt command

    run_dbt()

dbt_dag()
```
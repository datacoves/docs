## Set up postgres flexible server on Azure

1. Find it [here](https://portal.azure.com/#@datacoves.com/resource/subscriptions/91bd2205-0d74-42c9-86ad-41cca1b4822b/resourceGroups/datacoves/providers/Microsoft.DBforPostgreSQL/flexibleServers/datacoves-east-us/overview)
2. Connect to it using this command:

```
psql -h datacoves-east-us.postgres.database.azure.com -U dcmaster -d postgres
```

3. Create the `datacoves` user that will be used by Django:

```
CREATE USER datacoves password '<PASSWORD>';
ALTER USER datacoves CREATEDB CREATEROLE;
GRANT datacoves TO dcmaster;
CREATE DATABASE datacoves OWNER datacoves;
GRANT CONNECT ON DATABASE datacoves TO datacoves;
```

4. Dump data from internal Database

```
pg_dump -U postgres -h postgres-svc -d datacoves -Fc > dump.sql
```

5. Restore data on new Azure DB

```
pg_restore -U datacoves -h datacoves-east-us.postgres.database.azure.com -d datacoves --no-owner --role=datacoves dump.sql
```

6. Repeate steps 4 and 5 with the rest of the services that need to be migrated

Keep in mind that database objects owner could be changed, reassign the owner to the corresponding service account, i.e.:

```
REASSIGN OWNED BY datacoves TO dev123_airbyte;
```

If migrating `temporal` and `temporal_visibility` databases, you also need to update the database name on `schema_versions`.

7. Set `airbyte_db_external: true`, `airflow_db_external: true` and `superset_db_external: true` accordingly

8. Configure `postgres_db_provisioner` using the master user connection/credentials

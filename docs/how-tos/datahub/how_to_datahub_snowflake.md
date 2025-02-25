
# How to ingest Snowflake metadata into DataHub

Datahub can ingest Snowflake metadata by connecting to Snowflake directly.

## Configure DataHub Snowflake Source

To set up Snowflake ingestion in DataHub, follow these steps:

1. **Create a DataHub secret**: This example requires a secret named `svc_datahub_psw` for authentication. Ensure this secret is created before proceeding.
2. **Paste the YAML configuration**: In DataHub's Snowflake Ingestion wizard, switch to the **YAML view** and insert the following configuration.


```yaml
source:
    type: snowflake
    config:
        account_id: <your snowflake account withouth .snowflakecomputing.com >
        convert_urns_to_lowercase: true
        include_table_lineage: true
        include_view_lineage: true
        include_tables: true
        include_views: true
        include_usage_stats: true
        email_domain: example.com
        format_sql_queries: true
        profiling:
            enabled: true
            profile_table_level_only: false
            profile_if_updated_since_days: 1
        stateful_ingestion:
            enabled: true
            remove_stale_metadata: false
        warehouse: wh_catalog
        username: svc_datahub
        role: catalog
        password: '${svc_datahub_psw}'
        schema_pattern:
            deny:
                - DBT_ARTIFACTS
                - DBT_TEST__AUDIT
        database_pattern:
            allow:
                - '^(?!.*(?:PR|pr)).*$'
```

### Notes:
- The `database_pattern` setting excludes databases with `PR` or `pr` in their names.
- Ensure your Snowflake credentials and DataHub secrets are correctly set up before running the ingestion process.
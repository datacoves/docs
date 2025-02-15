
# How to ingest Snowflake metadata into DataHub

Datahub can ingest Snowflake metadata by connecting to Snowflake directly.

## Configure DataHub Snowflake Source

Here is a sample recipe for a Snowflake. You can click the `YAML` view in Datahub Snowflake Recipe and paste the following.

This recipe requires a Datahub secret to be created `svc_datahub_psw` so create that first.

```yaml
source:
    type: snowflake
    config:
        account_id: <your snowflake account withouth .snowflakecomputing.com >
        convert_urns_to_lowercase: false
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

Note in this example, the `database_pattern` has an allow pattern that actually excludes databases with `pr` or `PR` in the name.

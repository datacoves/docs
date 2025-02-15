
# How to ingest dbt metadata into DataHub

Datahub makes use of [dbt artifacts](https://datahubproject.io/docs/generated/ingestion/sources/dbt/#module-dbt) to populate metadata. This data comes from `catalog.json`, `manifest.json`, `run_results.json`, and `sources.json`

## Configure DataHub dbt Source

You must get the dbt artifacts to S3 first. Once the artifacts are on S3, you can proceed.

Configure the dbt source to ingest the dbt metadata. You can find more information on the [Datahub documentation](https://datahubproject.io/docs/generated/ingestion/sources/dbt/#config-details).

Here is a sample recipe for a dbt project.

This recipe requires a Datahub secret to be created `S3_secret_key` so create that first.

```yaml
source:
    type: dbt
    config:
        platform_instance: balboa
        manifest_path: 's3://<s3 bucket name>/dbt_artifacts/manifest.json'
        catalog_path: 's3://<s3 bucket name>/dbt_artifacts/catalog.json'
        sources_path: 's3://<s3 bucket name>/dbt_artifacts/sources.json'
        test_results_path: 's3://<s3 bucket name>/dbt_artifacts/run_results.json'
        target_platform: snowflake
        include_column_lineage: true
        convert_column_urns_to_lowercase: false
        aws_connection:
            aws_access_key_id: ABC.....
            aws_secret_access_key: '${S3_secret_key}'
            aws_region: us-west-2
        git_info:
            repo: github.com/datacoves/balboa
            url_template: '{repo_url}/blob/{branch}/transform/{file_path}'
```

## Configure DataHub a second dbt Source

If using Datacoves mesh(aka dbt Mesh), you can ingest metadata from more than one project. Note the exclusion of the upstream project. This will prevent Datahub from duplicating nodes.

```yaml
source:
    type: dbt
    config:
        platform_instance: great_bay
        manifest_path: 's3://<s3 bucket name>/dbt_artifacts_great_bay/manifest.json'
        catalog_path: 's3://<s3 bucket name>/dbt_artifacts_great_bay/catalog.json'
        sources_path: 's3://<s3 bucket name>/dbt_artifacts_great_bay/sources.json'
        test_results_path: 's3://<s3 bucket name>/dbt_artifacts_great_bay/run_results.json'
        target_platform: snowflake
        entities_enabled:
            sources: No
        stateful_ingestion:
            enabled: false
            remove_stale_metadata: true
        include_column_lineage: true
        convert_column_urns_to_lowercase: false
        skip_sources_in_lineage: true
        aws_connection:
            aws_access_key_id: ABC.....
            aws_secret_access_key: '${S3_secret_key}'
            aws_region: us-west-2
        git_info:
            repo: github.com/datacoves/great_bay
            url_template: '{repo_url}/blob/{branch}/transform/{file_path}'
        node_name_pattern:
            deny:
                - 'model.balboa.*'
                - 'seed.balboa.*'
```


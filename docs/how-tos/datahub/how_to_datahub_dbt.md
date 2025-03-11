# Ingesting dbt Metadata into DataHub

## Prerequisites

DataHub utilizes [dbt artifacts](https://datahubproject.io/docs/generated/ingestion/sources/dbt/#module-dbt) to populate metadata. Before configuring DataHub, ensure that dbt artifacts are available in an S3 bucket.  

These artifacts include:

- `catalog.json`
- `manifest.json`
- `run_results.json`
- `sources.json`

## Configuring the dbt Source in DataHub

To ingest dbt metadata, configure the dbt source in DataHub. Refer to the [official documentation](https://datahubproject.io/docs/generated/ingestion/sources/dbt/#config-details) for details.

### Sample Configuration

The following sample demonstrates how to configure a dbt ingestion source in DataHub. 

>[!NOTE] This configuration requires a DataHub secret (`S3_secret_key`) for secure access to S3. Ensure that this secret is created before proceeding.

```yaml
source:
  type: dbt
  config:
    platform_instance: balboa
    target_platform: snowflake
    manifest_path: "s3://<s3-bucket>/dbt_artifacts/manifest.json"
    catalog_path: "s3://<s3-bucket>/dbt_artifacts/catalog.json"
    sources_path: "s3://<s3-bucket>/dbt_artifacts/sources.json"
    test_results_path: "s3://<s3-bucket>/dbt_artifacts/run_results.json"
    include_column_lineage: true
    aws_connection:
      aws_access_key_id: ABC.....
      aws_secret_access_key: "${S3_secret_key}"
      aws_region: us-west-2
    git_info:
      repo: github.com/datacoves/balboa
      url_template: "{repo_url}/blob/{branch}/transform/{file_path}"

```
## Configuring DataHub for a Second dbt Source

When using **Datacoves Mesh** (also known as dbt Mesh), you can ingest metadata from multiple dbt projects. 

>[!NOTE] To prevent **duplicate nodes**, exclude the upstream project by specifying patterns to deny in the `node_name_pattern` section.

### Sample Configuration

The following configuration demonstrates how to add a second dbt source in DataHub:

```yaml
source:
  type: dbt
  config:
    platform_instance: great_bay
    target_platform: snowflake
    manifest_path: "s3://<s3-bucket>/dbt_artifacts_great_bay/manifest.json"
    catalog_path: "s3://<s3-bucket>/dbt_artifacts_great_bay/catalog.json"
    sources_path: "s3://<s3-bucket>/dbt_artifacts_great_bay/sources.json"
    test_results_path: "s3://<s3-bucket>/dbt_artifacts_great_bay/run_results.json"
    
    # Prevent duplication of upstream nodes
    entities_enabled:
      sources: No

    # Stateful ingestion settings
    stateful_ingestion:
      enabled: false
      remove_stale_metadata: true

    include_column_lineage: true
    convert_column_urns_to_lowercase: false
    skip_sources_in_lineage: true

    # AWS credentials (requires secret `S3_secret_key`)
    aws_connection:
      aws_access_key_id: ABC.....
      aws_secret_access_key: "${S3_secret_key}"
      aws_region: us-west-2

    # Git repository information
    git_info:
      repo: github.com/datacoves/great_bay
      url_template: "{repo_url}/blob/{branch}/transform/{file_path}"

    # Exclude upstream dbt project nodes to prevent duplication
    node_name_pattern:
      deny:
        - "model.balboa.*"
        - "seed.balboa.*"
```
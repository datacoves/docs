defmodule Datacoves.Repo.Migrations.CreateEnvironments do
  use Ecto.Migration

  def change do
    create table(:projects_environment) do
      add :airbyte_config, :binary
      add :airflow_config, :binary
      add :cluster_id, :integer
      add :project_id, references(:projects_project)
      add :dbt_docs_config, :binary
      add :dbt_home_path, :string
      add :dbt_profiles_dir, :string
      add :docker_config_secret_name, :string
      add :docker_config, :binary
      add :docker_registry, :string
      add :internal_services, :map
      add :minio_config, :binary
      add :name, :string
      add :pomerium_config, :binary
      add :profile_id, :integer
      add :quotas, :map
      add :release_id, :integer
      add :release_profile, :string
      add :services, :map
      add :settings, :map
      add :slug, :string
      add :superset_config, :binary
      add :sync, :boolean
      add :type, :string
      add :update_strategy, :string
      add :workspace_generation, :integer

      add :created_at, :utc_datetime
      add :updated_at, :utc_datetime
    end
  end
end

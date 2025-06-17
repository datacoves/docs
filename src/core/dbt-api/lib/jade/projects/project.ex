defmodule Jade.Projects.Project do
  use Jade, :schema

  embedded_schema do
    field :name, :string
    field :slug, :string
    field :account_id, :integer
    field :connection_id, :integer
    # has_one :connection, NotImplemented
    field :repository_id, :integer
    # has_one :repository, NotImplemented
    field :semantic_layer_id, :integer

    # The dbt/Datacoves Project ID
    field :integration_entity_id, :integer

    field :skipped_setup, :boolean
    field :state, :integer
    field :dbt_project_subdirectory, :string

    # has_one :group_permissions, NotImplemented

    field :docs_job_id, :integer
    # has_one :docs_job, NotImplemented

    field :freshness_job_id, :integer
    # has_one :freshness_job, NotImplemented

    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime
  end
end

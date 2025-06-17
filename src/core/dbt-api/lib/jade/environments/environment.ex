defmodule Jade.Environments.Environment do
  @moduledoc """
  The dbt Cloud Environment Schema. Its data comes from the Datacoves database.
  """
  use Jade, :schema

  embedded_schema do
    field :account_id, :integer
    field :project_id, :integer
    field :connection_id, :integer
    # belongs_to :connection, NotImplemented
    field :credentials_id, :integer
    field :created_by_id, :integer
    field :extended_attributes_id, :integer
    field :repository_id, :integer
    # belongs_to :repository, NotImplemented
    field :name, :string
    field :slug, :string
    field :airflow_config, :map
    field :dbt_project_subdirectory, :string
    field :services, :map
    field :use_custom_branch, :string
    field :custom_branch, :string
    field :dbt_version, :string
    field :raw_dbt_version, :string
    field :supports_docs, :boolean, default: false
    field :state, :integer
    field :custom_environment_variables, :string
    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime
  end
end

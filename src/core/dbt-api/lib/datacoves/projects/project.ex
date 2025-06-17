defmodule Datacoves.Projects.Project do
  @moduledoc """
  The Project schema as stored in the Datacoves Postgres database.
  """
  use Datacoves, :schema

  schema "projects_project" do
    field :ci_home_url, :string
    field :ci_provider, :string
    field :clone_strategy, :string
    field :deploy_credentials, :binary
    field :deploy_key_id, :integer
    field :name, :string
    field :release_branch, :string
    field :repository_id, :integer
    field :settings, :map
    field :slug, :string
    field :validated_at, :utc_datetime
    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime

    belongs_to :account, Datacoves.Accounts.Account
    has_many :environments, Datacoves.Environments.Environment
  end
end

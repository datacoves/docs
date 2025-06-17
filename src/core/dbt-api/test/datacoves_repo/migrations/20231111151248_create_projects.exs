defmodule Datacoves.Repo.Migrations.CreateProjects do
  use Ecto.Migration

  def change do
    create table(:projects_project) do
      add :ci_home_url, :string
      add :ci_provider, :string
      add :clone_strategy, :string
      add :deploy_credentials, :binary
      add :deploy_key_id, :integer
      add :name, :string
      add :release_branch, :string
      add :repository_id, :integer
      add :settings, :map
      add :slug, :string
      add :validated_at, :utc_datetime
      add :created_at, :utc_datetime
      add :updated_at, :utc_datetime

      add :account_id, references(:users_account)
    end
  end
end

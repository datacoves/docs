defmodule Datacoves.Repo.Migrations.CreateExtendedGroups do
  use Ecto.Migration

  def change do
    create table(:users_extendedgroup) do
      add :name, :string
      add :identity_groups, {:array, :string}
      add :role, :string

      add :account_id, references(:users_account)
      add :group_id, references(:auth_group)
      add :environment_id, references(:projects_environment)
      add :project_id, references(:projects_project)
    end
  end
end

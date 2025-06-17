defmodule Datacoves.Repo.Migrations.CreateUsersUserGroups do
  use Ecto.Migration

  def change do
    create table(:users_user_groups) do
      add :user_id, references(:users_user)
      add :group_id, references(:auth_group)
    end
  end
end

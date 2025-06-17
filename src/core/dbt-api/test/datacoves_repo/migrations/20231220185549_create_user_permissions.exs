defmodule Datacoves.Repo.Migrations.CreateUserPermissions do
  use Ecto.Migration

  def change do
    create table(:users_user_user_permissions) do
      add :user_id, references(:users_user)
      add :permission_id, references(:auth_permission)
    end
  end
end

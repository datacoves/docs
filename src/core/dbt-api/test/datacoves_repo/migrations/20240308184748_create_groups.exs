defmodule Datacoves.Repo.Migrations.CreateGroups do
  use Ecto.Migration

  def change do
    create table(:auth_group) do
      add :name, :string

      add :user_id, references(:users_user)
    end
  end
end

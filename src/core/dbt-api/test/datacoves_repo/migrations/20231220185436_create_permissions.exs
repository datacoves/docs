defmodule Datacoves.Repo.Migrations.CreatePermissions do
  use Ecto.Migration

  def change do
    create table(:auth_permission) do
      add :name, :string
      add :content_type_id, :integer
      add :codename, :string
    end
  end
end

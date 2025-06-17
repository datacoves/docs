defmodule Datacoves.Repo.Migrations.CreateUsers do
  use Ecto.Migration

  def change do
    create table(:users_user) do
      add :eid, :binary_id
      add :created_at, :utc_datetime
      add :updated_at, :utc_datetime
      add :password, :string
      add :last_login, :utc_datetime
      add :email, :string
      add :name, :string
      add :avatar, :string
      add :deactivated_at, :utc_datetime
      add :is_superuser, :boolean
      add :settings, :map
      add :is_service_account, :boolean
      add :slug, :string
    end
  end
end

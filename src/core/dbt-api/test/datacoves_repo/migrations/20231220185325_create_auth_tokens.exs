defmodule Datacoves.Repo.Migrations.CreateAuthTokens do
  use Ecto.Migration

  def change do
    create table(:authtoken_token, primary_key: false) do
      add :key, :string, primary_key: true
      add :created, :utc_datetime

      add :user_id, references(:users_user, on_delete: :delete_all)
    end
  end
end

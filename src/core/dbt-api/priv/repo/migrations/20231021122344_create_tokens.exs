defmodule Jade.Repo.Migrations.CreateTokens do
  use Ecto.Migration

  def change do
    create table(:tokens) do
      add(:account_id, :integer)
      add(:key_hash, :string)

      timestamps(type: :utc_datetime)
    end

    create(unique_index(:tokens, [:key_hash]))
    create(unique_index(:tokens, [:account_id]))
  end
end

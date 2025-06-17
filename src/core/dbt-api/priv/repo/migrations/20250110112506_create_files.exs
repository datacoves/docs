defmodule Jade.Repo.Migrations.CreateFiles do
  use Ecto.Migration

  def change do
    create table(:files) do
      add :slug, :binary_id, default: fragment("gen_random_uuid()"), null: false
      add :filename, :string
      add :environment_slug, :string
      add :tag, :string
      add :path, :string

      timestamps(type: :utc_datetime)
    end

    create unique_index(:files, [:slug])
    create unique_index(:files, [:environment_slug, :tag])
  end
end

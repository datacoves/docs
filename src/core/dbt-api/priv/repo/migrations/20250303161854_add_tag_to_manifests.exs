defmodule Jade.Repo.Migrations.AddTagToManifests do
  use Ecto.Migration

  def change do
    alter table(:manifests) do
      add :tag, :string
    end

    create unique_index(:manifests, [:environment_slug, :tag])
  end
end

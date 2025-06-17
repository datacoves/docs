defmodule Jade.Repo.Migrations.AddProjectIdToManifests do
  use Ecto.Migration

  def change do
    alter table(:manifests) do
      add :project_id, :integer
    end

    create index(:manifests, [:project_id])
  end
end

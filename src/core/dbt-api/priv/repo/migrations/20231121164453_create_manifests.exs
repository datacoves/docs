defmodule Jade.Repo.Migrations.CreateManifests do
  use Ecto.Migration

  def change do
    create table(:manifests) do
      add :slug, :binary_id, default: fragment("gen_random_uuid()"), null: false
      add :account_id, :integer
      add :environment_slug, :string
      add :dag_id, :string
      add :dag_run_id, :integer
      add :dag_run_run_id, :string
      add :job_run_id, references(:job_run_ids, on_delete: :nothing)
      add :content, :jsonb

      timestamps(type: :utc_datetime)
    end

    create index(:manifests, [:account_id, :job_run_id])
  end
end

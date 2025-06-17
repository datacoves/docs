defmodule Jade.Repo.Migrations.CreateJobRunIds do
  use Ecto.Migration

  def change do
    create table(:job_run_ids) do
      add(:environment_id, :integer)
      add(:dag_run_id, :integer)
    end

    create(unique_index(:job_run_ids, [:environment_id, :dag_run_id]))
  end
end

defmodule Airflow.Repo.Migrations.CreateDagRuns do
  use Ecto.Migration

  def change do
    create table(:dag_run) do
      add :dag_id, :string
      add :execution_date, :utc_datetime
      add :state, :string
      add :run_id, :string
      add :external_trigger, :boolean
      add :conf, :binary
      add :end_date, :utc_datetime
      add :start_date, :utc_datetime
      add :run_type, :string
      add :last_scheduling_decision, :utc_datetime
      add :dag_hash, :string
      add :creating_job_id, :integer
      add :queued_at, :utc_datetime
      add :data_interval_start, :utc_datetime
      add :data_interval_end, :utc_datetime
      add :log_template_id, :integer
    end
  end
end

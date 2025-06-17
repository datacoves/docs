defmodule Airflow.Repo.Migrations.CreateDags do
  use Ecto.Migration

  def change do
    create table(:dag, primary_key: false) do
      add :dag_id, :string, primary_key: true
      add :default_view, :string
      add :description, :string
      add :fileloc, :string
      add :has_import_errors, :boolean, default: false
      add :has_task_concurrency_limits, :boolean
      add :is_active, :boolean, default: true
      add :is_paused, :boolean, default: false
      add :is_subdag, :boolean, default: false
      add :last_expired, :utc_datetime
      add :last_parsed_time, :utc_datetime
      add :last_pickled, :utc_datetime
      add :max_active_runs, :integer
      add :max_active_tasks, :integer
      add :next_dagrun_create_after, :utc_datetime
      add :next_dagrun_data_interval_end, :utc_datetime
      add :next_dagrun_data_interval_start, :utc_datetime
      add :next_dagrun, :utc_datetime
      add :owners, :string
      add :pickle_id, :integer
      add :root_dag_id, :string
      add :schedule_interval, :string
      add :scheduler_lock, :boolean
      add :timetable_description, :string
    end
  end
end

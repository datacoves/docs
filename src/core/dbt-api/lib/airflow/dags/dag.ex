defmodule Airflow.Dags.Dag do
  @moduledoc """
  The DAG schema as stored in the Airflow Postgres database.
  """
  use Airflow, :schema

  @primary_key false
  schema "dag" do
    field :dag_id, :string, primary_key: true
    field :default_view, :string
    field :description, :string
    field :fileloc, :string
    field :has_import_errors, :boolean, default: false
    field :has_task_concurrency_limits, :boolean
    field :is_active, :boolean, default: true
    field :is_paused, :boolean, default: false
    field :is_subdag, :boolean, default: false
    field :last_expired, :utc_datetime
    field :last_parsed_time, :utc_datetime
    field :last_pickled, :utc_datetime
    field :max_active_runs, :integer
    field :max_active_tasks, :integer
    field :next_dagrun_create_after, :utc_datetime
    field :next_dagrun_data_interval_end, :utc_datetime
    field :next_dagrun_data_interval_start, :utc_datetime
    field :next_dagrun, :utc_datetime
    field :owners, :string
    field :pickle_id, :integer
    field :root_dag_id, :string
    field :schedule_interval, :string
    field :scheduler_lock, :boolean
    field :timetable_description, :string

    has_many :dag_runs, Airflow.DagRuns.DagRun, foreign_key: :dag_id, references: :dag_id

    has_one :most_recent_dag_run, Airflow.DagRuns.DagRun,
      foreign_key: :dag_id,
      references: :dag_id

    has_one :most_recent_completed_dag_run, Airflow.DagRuns.DagRun,
      foreign_key: :dag_id,
      references: :dag_id
  end
end

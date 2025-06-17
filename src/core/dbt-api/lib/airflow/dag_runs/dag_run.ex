defmodule Airflow.DagRuns.DagRun do
  @moduledoc """
  The DAGRun schema as stored in the Airflow Postgres database.

  The "State" is defined here: https://github.com/apache/airflow/blob/d4002261b57236ffdca9a5790097f295794965cf/airflow/utils/state.py#L73
  """
  use Airflow, :schema

  @valid_statuses [:queued, :running, :success, :failed]

  schema "dag_run" do
    belongs_to :dag, Airflow.Dags.Dag, references: :dag_id, type: :string

    field :execution_date, :utc_datetime
    field :state, Ecto.Enum, values: @valid_statuses
    field :run_id, :string
    field :external_trigger, :boolean
    field :conf, :binary
    field :end_date, :utc_datetime
    field :start_date, :utc_datetime
    field :run_type, :string
    field :last_scheduling_decision, :utc_datetime
    field :dag_hash, :string
    field :creating_job_id, :integer
    field :queued_at, :utc_datetime
    field :data_interval_start, :utc_datetime
    field :data_interval_end, :utc_datetime
    field :log_template_id, :integer
  end

  def valid_statuses(), do: @valid_statuses
end

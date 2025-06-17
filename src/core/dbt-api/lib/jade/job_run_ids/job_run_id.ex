defmodule Jade.JobRunIds.JobRunId do
  @moduledoc """
  This schema serves as a mapper from a composite primary key of
  Datacoves Environment ID and Airflow DagRun ID to a globally unique integer,
  the primary key of this schema.

  The problem this mapper solves is that we might have multiple Airflow Databases
  which might have the same integer ID for different DagRuns. For example,
  two Airflow Databases might have a DagRun with ID: 1. This mapper stores
  the Datacoves Environment for the Airflow Postgres and Airflow's DagRun ID so
  that we can fetch the DagRun from the correct Environment/Airflow database if
  somebody requests it.

  This mapper is created when we list all DagRuns of an environment/airflow database.
  """
  use Jade, :schema

  schema "job_run_ids" do
    field :environment_id, :integer
    field :dag_run_id, :integer
  end

  def changeset(record, attrs) do
    record
    |> cast(attrs, [:environment_id, :dag_run_id])
    |> validate_required([:environment_id, :dag_run_id])
  end
end

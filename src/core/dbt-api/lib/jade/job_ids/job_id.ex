defmodule Jade.JobIds.JobId do
  @moduledoc """
  This schema serves as a mapper from Airflow string-based IDs to an integer ID
  that we define ourselves. This way, we can query for Airflow DAGs using integer
  IDs like we already do with DAGRuns/JobRuns, Projects, and Accounts as well.

  Each record keeps a map of Airflow ID + Datacoves Environment ID -> Generated Integer ID,
  the primary key of the record. If an Airflow ID changes, a new record will 
  be created. 
  """
  use Jade, :schema

  schema "job_ids" do
    field :environment_id, :integer
    field :dag_id, :string
  end

  def changeset(record, attrs) do
    record
    |> cast(attrs, [:environment_id, :dag_id])
    |> validate_required([:environment_id, :dag_id])
  end
end

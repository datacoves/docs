defmodule Airflow.Dags.DagRepo do
  @moduledoc """
  The Repository for fetching DAGs from the Airflow Database.
  """
  use Airflow, :repository

  alias Airflow.Dags.Dag

  def list(environment, _params) do
    Repo.with_dynamic_repo(
      environment,
      fn -> Repo.all(Dag) end,
      fn -> [] end
    )
  end

  def get(environment, dag_id) do
    Repo.with_dynamic_repo(
      environment,
      fn ->
        Dag
        |> Repo.get(dag_id)
        |> Repo.normalize_one()
      end
    )
  end
end

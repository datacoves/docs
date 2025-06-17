defmodule Airflow.DagRuns.DagRunRepo do
  @moduledoc """
  The Repository for fetching DAGRuns from the Airflow Database.
  """
  use Airflow, :repository

  alias Airflow.DagRuns.DagRun

  def list(environment) do
    Repo.with_dynamic_repo(
      environment,
      fn -> Repo.all(DagRun) end,
      fn -> [] end
    )
  end

  def get(environment, dag_run_id) do
    Repo.with_dynamic_repo(
      environment,
      fn ->
        DagRun
        |> Repo.get(dag_run_id)
        |> Repo.normalize_one()
      end
    )
  end

  def get_by(environment, attrs) do
    Repo.with_dynamic_repo(
      environment,
      fn ->
        DagRun
        |> where(^attrs)
        |> Repo.one()
        |> Repo.normalize_one()
      end
    )
  end

  def get_most_recent(environment, state \\ nil) do
    Repo.with_dynamic_repo(
      environment,
      fn ->
        from(dag_run in DagRun,
          as: :dag_run,
          where: not is_nil(dag_run.end_date),
          order_by: [desc_nulls_last: dag_run.end_date],
          limit: 1
        )
        |> maybe_filter_state(state)
        |> Repo.one()
        |> Repo.normalize_one()
      end
    )
  end

  def get_most_recent_for_dag(environment, dag_id, state \\ nil) do
    Repo.with_dynamic_repo(
      environment,
      fn ->
        from(dag_run in DagRun,
          as: :dag_run,
          where: dag_run.dag_id == ^dag_id,
          order_by: [desc_nulls_last: dag_run.end_date],
          limit: 1
        )
        |> maybe_filter_state(state)
        |> Repo.one()
        |> Repo.normalize_one()
      end
    )
  end

  defp maybe_filter_state(query, nil), do: query

  defp maybe_filter_state(query, state) do
    where(query, [dag_run: dag_run], dag_run.state == ^state)
  end
end

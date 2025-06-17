defmodule Airflow.Repo do
  use Ecto.Repo,
    otp_app: :jade,
    adapter: Ecto.Adapters.Postgres,
    read_only: Mix.env() != :test

  require Ecto.Query

  @doc """
  Sets the correct dynamic repo on Airflow.Repo before making
  a Database Request to an Airflow Postgres pod. If no Repo runs
  for the given Environment, Airflow.Repos tries to start a new one
  but returns `{:error, :not_found}` if it fails. Also, if the
  environment has services -> airflow disabled, it returns
  `{:error, :not_found}` immediately.
  """
  def with_dynamic_repo(environment, callback, fallback \\ nil) do
    case Airflow.Repos.get_repo_for_environment(environment) do
      {:ok, pid} ->
        Airflow.Repo.put_dynamic_repo(pid)
        callback.()

      {:error, :not_found, _message} = error ->
        if fallback, do: fallback.(), else: error
    end
  end

  def normalize_one(nil), do: {:error, :not_found}
  def normalize_one(record), do: {:ok, record}

  def paginate(query, params) do
    query
    |> maybe_add_offset(params)
    |> maybe_add_limit(params)
  end

  defp maybe_add_offset(query, %{offset: offset}) when is_integer(offset) and offset >= 0 do
    Ecto.Query.offset(query, ^offset)
  end

  defp maybe_add_offset(query, _params), do: query

  defp maybe_add_limit(query, %{limit: limit}) when is_integer(limit) and limit >= 0 do
    Ecto.Query.limit(query, ^limit)
  end

  defp maybe_add_limit(query, _params), do: query
end

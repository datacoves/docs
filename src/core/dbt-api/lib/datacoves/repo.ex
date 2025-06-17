defmodule Datacoves.Repo do
  use Ecto.Repo,
    otp_app: :jade,
    adapter: Ecto.Adapters.Postgres,
    read_only: Mix.env() != :test

  require Ecto.Query

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

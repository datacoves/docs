defmodule Jade.Repo do
  use Ecto.Repo,
    otp_app: :jade,
    adapter: Ecto.Adapters.Postgres

  @doc """
  A small wrapper around `Repo.transaction/2'.

  Commits the transaction if the lambda returns `:ok` or `{:ok, result}`,
  rolling it back if the lambda returns `:error` or `{:error, reason}`. In both
  cases, the function returns the result of the lambda.
  """
  @spec transact((-> any()), keyword()) :: {:ok, any()} | {:error, any()}
  def transact(fun, opts \\ []) do
    transaction(
      fn ->
        case fun.() do
          {:ok, value} -> value
          :ok -> :transaction_commited
          {:error, reason} -> rollback(reason)
          :error -> rollback(:transaction_rollback_error)
        end
      end,
      opts
    )
  end

  def normalize_all([]), do: {:error, :not_found}
  def normalize_all(records), do: {:ok, records}

  def normalize_one(nil), do: {:error, :not_found}
  def normalize_one([]), do: {:error, :not_found}
  def normalize_one([record | _]), do: {:ok, record}
  def normalize_one(record), do: {:ok, record}
end

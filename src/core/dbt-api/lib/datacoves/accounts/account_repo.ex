defmodule Datacoves.Accounts.AccountRepo do
  @moduledoc """
  The Project repository for fetching Account data from
  the Datacoves Postgres database.

  The Datacoves.Repo connection is read-only, so this
  repository offers no write operations.

  Our API receives requests from individual users/accounts only,
  so we don't need to list all accounts, but only fetch the
  account of the requesting user. That's why we only have a `get/1`
  function and no `list/1` function as in other repositories.
  """
  use Datacoves, :repository

  alias Datacoves.Accounts.Account

  def get(account_id) do
    Account
    |> Repo.get(account_id)
    |> Repo.normalize_one()
  end
end

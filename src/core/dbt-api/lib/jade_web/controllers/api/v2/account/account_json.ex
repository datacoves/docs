defmodule JadeWeb.API.V2.AccountJSON do
  @moduledoc """
  The Account JSON component.

  Renders one or multiple Accounts to a map.
  """

  def index(%{accounts: accounts}) do
    %{data: data(accounts)}
  end

  def show(%{account: account}) do
    %{data: data(account)}
  end

  defp data(accounts) when is_list(accounts) do
    for account <- accounts, do: data(account)
  end

  defp data(account) do
    Map.from_struct(account)
  end
end

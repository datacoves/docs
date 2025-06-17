defmodule Datacoves.Users.UserRepo do
  @moduledoc """
  The repository for the Datacoves' User schema.
  """

  use Datacoves, :repository

  alias Datacoves.Users.User

  def get_extended_groups(%User{} = user) do
    user = Repo.preload(user, groups: [:extended_group])

    user.groups
    |> Enum.map(fn group -> group.extended_group end)
    |> Enum.reject(&is_nil/1)
  end
end

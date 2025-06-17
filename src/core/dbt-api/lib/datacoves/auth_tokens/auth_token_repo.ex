defmodule Datacoves.AuthTokens.AuthTokenRepo do
  @moduledoc """
  The AuthToken repository for fetching tokens from the Datacoves database.
  """

  use Datacoves, :repository

  alias Datacoves.AuthTokens.AuthToken

  @default_preloads [
    user: [:permissions, groups: [extended_group: [:account, :project, :environment]]]
  ]

  def get_by(attrs, preloads \\ @default_preloads) do
    AuthToken
    |> where(^attrs)
    |> preload(^preloads)
    |> Repo.one()
    |> Repo.normalize_one()
  end
end

defmodule Datacoves.AuthTokens.AuthToken do
  @moduledoc """
  The AuthToken schema as stored in the Datacoves Postgres database.
  """
  use Datacoves, :schema

  @primary_key false
  schema "authtoken_token" do
    field :key, :string, primary_key: true
    field :created, :utc_datetime

    belongs_to :user, Datacoves.Users.User
  end
end

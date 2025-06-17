defmodule Datacoves.Users.User do
  @moduledoc """
  The User schema as stored in the Datacoves database.
  """
  use Datacoves, :schema

  schema "users_user" do
    field :eid, :binary_id
    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime
    field :password, :string
    field :last_login, :utc_datetime
    field :email, :string
    field :name, :string
    field :avatar, :string
    field :deactivated_at, :utc_datetime
    field :is_superuser, :boolean
    field :settings, :map
    field :is_service_account, :boolean
    field :slug, :string

    has_many :auth_tokens, Datacoves.AuthTokens.AuthToken

    many_to_many :permissions, Datacoves.Permissions.Permission, join_through: "users_user_user_permissions"

    many_to_many :groups, Datacoves.Groups.Group, join_through: "users_user_groups"
  end
end

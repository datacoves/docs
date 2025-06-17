defmodule Datacoves.Permissions.Permission do
  @moduledoc """
  The Permission schema as stored in the Datacoves database.
  """

  use Datacoves, :schema

  schema "auth_permission" do
    field :name, :string
    field :content_type_id, :integer
    field :codename, :string

    many_to_many :users, Datacoves.Users.User, join_through: "users_user_user_permissions"
  end
end

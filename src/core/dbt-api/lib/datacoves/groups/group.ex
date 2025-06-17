defmodule Datacoves.Groups.Group do
  @moduledoc """
  The Group schema as stored in the Datacoves database.
  """

  use Datacoves, :schema

  schema "auth_group" do
    field :name, :string

    many_to_many :users, Datacoves.Users.User, join_through: "users_user_groups"
    has_one :extended_group, Datacoves.Groups.ExtendedGroup
  end
end

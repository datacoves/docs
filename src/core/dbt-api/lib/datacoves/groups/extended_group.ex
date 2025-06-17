defmodule Datacoves.Groups.ExtendedGroup do
  @moduledoc """
  The ExtendedGroup schema as stored in the Datacoves database.
  """

  use Datacoves, :schema

  schema "users_extendedgroup" do
    field :name, :string
    field :identity_groups, {:array, :string}
    field :role, :string

    belongs_to :group, Datacoves.Groups.Group
    belongs_to :account, Datacoves.Accounts.Account
    belongs_to :environment, Datacoves.Environments.Environment
    belongs_to :project, Datacoves.Projects.Project
  end
end

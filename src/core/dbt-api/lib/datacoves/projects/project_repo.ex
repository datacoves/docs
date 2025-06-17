defmodule Datacoves.Projects.ProjectRepo do
  @moduledoc """
  The Project repository for fetching Project data from
  the Datacoves Postgres database.

  The Datacoves.Repo connection is read-only, so this
  repository offers no write operations.
  """
  use Datacoves, :repository

  alias Datacoves.Projects.Project

  def list(%{account_id: account_id} = params) do
    Project
    |> where(account_id: ^account_id)
    |> Repo.paginate(params)
    |> Repo.all()
  end

  def get_by(attrs) do
    Project
    |> where(^attrs)
    |> Repo.one()
    |> Repo.normalize_one()
  end
end

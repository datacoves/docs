defmodule Datacoves.Environments.EnvironmentRepo do
  @moduledoc """
  The Environment repository for fetching Environment data from
  the Datacoves Postgres database.

  The Datacoves.Repo connection is read-only, so this
  repository offers no write operations.
  """
  use Datacoves, :repository

  alias Datacoves.Environments.Environment

  @default_preloads [:project]

  def list(), do: Environment |> Repo.all() |> Repo.preload(@default_preloads)

  def list(%{account_id: account_id, project_id: project_id} = params) do
    account_id
    |> base_query()
    |> where([project: project], project.id == ^project_id)
    |> Repo.paginate(params)
    |> Repo.all()
  end

  def list(%{account_id: account_id} = params) do
    account_id
    |> base_query()
    |> Repo.paginate(params)
    |> Repo.all()
  end

  def get(account_id, environment_id) do
    account_id
    |> base_query()
    |> Repo.get(environment_id)
    |> Repo.normalize_one()
  end

  def get_by(attrs) do
    Environment
    |> where(^attrs)
    |> preload(^@default_preloads)
    |> Repo.one()
    |> Repo.normalize_one()
  end

  defp base_query(account_id) do
    from(environment in Environment,
      join: project in assoc(environment, :project),
      as: :project,
      where: project.account_id == ^account_id,
      preload: ^@default_preloads
    )
  end
end

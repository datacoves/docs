defmodule Jade.Projects.ProjectRepo do
  @moduledoc """
  The Repository for Projects.

  Fetches the Project data from the defined adapter. 
  The adapter fetches the project data from the Datacoves Postgres
  database or mocks them in our tests. We convert the Datacoves
  Project schema to the Jade Project schema before returning it.
  """

  alias Datacoves.Projects.Project, as: DatacovesProject
  alias Datacoves.Projects.ProjectRepo

  alias Jade.Projects.Project, as: JadeProject

  @spec list(map()) :: list(JadeProject.t())
  def list(params) do
    ProjectRepo.list(params) |> convert()
  end

  @spec get(integer(), integer()) :: {:ok, JadeProject.t()} | {:error, :not_found}
  def get(account_id, project_id) do
    with {:ok, project} <- ProjectRepo.get_by(id: project_id, account_id: account_id) do
      {:ok, convert(project)}
    end
  end

  @spec get_by(keyword()) :: {:ok, JadeProject.t()} | {:error, :not_found}
  def get_by(attrs) do
    with {:ok, project} <- ProjectRepo.get_by(attrs) do
      {:ok, convert(project)}
    end
  end

  defp convert(projects) when is_list(projects) do
    Enum.map(projects, &convert/1)
  end

  defp convert(%DatacovesProject{} = project) do
    %JadeProject{
      id: project.id,
      # Fields needed by BigEye
      account_id: project.account_id,
      name: project.name,
      slug: project.slug,
      integration_entity_id: project.id,
      # ----------------------
      # TODO: Decide on which Environment of many to use here.
      connection_id: nil,
      repository_id: project.repository_id,
      semantic_layer_id: nil,
      skipped_setup: false,
      state: nil,
      # TODO: Fetch from Environment, but which one?
      dbt_project_subdirectory: nil,
      docs_job_id: nil,
      freshness_job_id: nil,
      created_at: project.created_at,
      updated_at: project.updated_at
    }
  end
end

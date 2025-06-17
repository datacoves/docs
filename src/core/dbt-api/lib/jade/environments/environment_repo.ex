defmodule Jade.Environments.EnvironmentRepo do
  @moduledoc """
  The Repository for Environments.
  """

  alias Datacoves.Environments.Environment, as: DatacovesEnvironment
  alias Datacoves.Environments.EnvironmentRepo

  alias Jade.Environments.Environment

  @spec list() :: [Environment.t()]
  def list(), do: EnvironmentRepo.list() |> convert()

  @spec list(map()) :: list(Environment.t())
  def list(params) do
    EnvironmentRepo.list(params) |> convert()
  end

  @spec get(integer(), integer()) :: {:ok, Environment.t()} | {:error, :not_found}
  def get(account_id, environment_id) do
    with {:ok, datacoves_environment} <- EnvironmentRepo.get(account_id, environment_id) do
      {:ok, convert(datacoves_environment)}
    end
  end

  @spec get_by_slug(binary()) :: {:ok, Environment.t()} | {:error, :not_found}
  def get_by_slug(slug) do
    with {:ok, datacoves_environment} <- EnvironmentRepo.get_by(slug: slug) do
      {:ok, convert(datacoves_environment)}
    end
  end

  defp convert(environments) when is_list(environments) do
    Enum.map(environments, &convert/1)
  end

  defp convert(%DatacovesEnvironment{} = environment) do
    airflow_config = DatacovesEnvironment.decrypt_json_field!(environment, :airflow_config)

    %Environment{
      id: environment.id,
      account_id: environment.project.account_id,
      connection_id: environment.id,
      project_id: environment.project_id,
      credentials_id: nil,
      created_by_id: nil,
      extended_attributes_id: nil,
      repository_id: nil,
      name: environment.name,
      slug: environment.slug,
      airflow_config: airflow_config,
      dbt_project_subdirectory: environment.dbt_home_path,
      services: environment.services,
      use_custom_branch: false,
      custom_branch: nil,
      dbt_version: nil,
      raw_dbt_version: nil,
      supports_docs: nil,
      state: nil,
      custom_environment_variables: nil,
      created_at: environment.created_at,
      updated_at: environment.updated_at
    }
  end
end

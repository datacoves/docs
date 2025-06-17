defmodule JadeWeb.API.V2.EnvironmentJSON do
  @moduledoc """
  The Environment JSON component.

  Renders one or multiple Environmentss to a map.
  """

  def index(%{environments: environments}) do
    %{data: data(environments)}
  end

  def show(%{environment: environment}) do
    %{data: data(environment)}
  end

  defp data(environments) when is_list(environments) do
    for environment <- environments, do: data(environment)
  end

  defp data(environment) do
    environment |> Map.from_struct() |> Map.drop([:services, :airflow_config])
  end
end

defmodule JadeWeb.API.V2.ProjectJSON do
  @moduledoc """
  The Project JSON component.

  Renders one or multiple Projects to a map.
  """

  def index(%{projects: projects}) do
    %{data: data(projects)}
  end

  def show(%{project: project}) do
    %{data: data(project)}
  end

  defp data(projects) when is_list(projects) do
    for project <- projects, do: data(project)
  end

  defp data(project) do
    Map.from_struct(project)
  end
end

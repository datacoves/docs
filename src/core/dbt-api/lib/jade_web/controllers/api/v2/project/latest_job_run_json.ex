defmodule JadeWeb.API.V2.Project.LatestJobRunJSON do
  @moduledoc """
  The latest JobRun JSON component.

  Renders the latest JobRun for a given Project.
  """

  def show(%{job_run: job_run}) do
    %{data: data(job_run)}
  end

  def data(job_run) do
    job_run |> Map.from_struct() |> Map.delete(:job)
  end
end

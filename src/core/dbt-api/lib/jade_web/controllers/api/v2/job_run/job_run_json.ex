defmodule JadeWeb.API.V2.JobRunJSON do
  @moduledoc """
  The JobRun JSON component.

  Renders one or multiple JobRuns to a map.
  """

  alias Jade.JobRuns.JobRun

  def index(%{job_runs: job_runs}) do
    %{data: build(job_runs)}
  end

  def show(%{job_run: job_run}) do
    %{data: build(job_run)}
  end

  def build(job_runs) when is_list(job_runs) do
    for job_run <- job_runs, do: build(job_run)
  end

  def build(%JobRun{} = job_run) do
    job_run |> Map.from_struct() |> Map.delete(:job)
  end

  def build(_job_run), do: nil
end

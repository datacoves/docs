defmodule JadeWeb.API.V2.JobJSON do
  @moduledoc """
  The Job JSON component.

  Renders one or multiple Jobs to a map.
  """

  alias JadeWeb.API.V2.JobRunJSON

  def index(%{jobs: jobs}) do
    %{data: build(jobs)}
  end

  def show(%{job: job}) do
    %{data: build(job)}
  end

  def build(jobs) when is_list(jobs) do
    for job <- jobs, do: build(job)
  end

  def build(job) do
    job
    |> Map.from_struct()
    |> Map.put(:most_recent_job_run, JobRunJSON.build(job.most_recent_job_run))
    |> Map.put(
      :most_recent_completed_job_run,
      JobRunJSON.build(job.most_recent_completed_job_run)
    )
  end
end

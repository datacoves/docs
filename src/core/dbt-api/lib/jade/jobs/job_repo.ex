defmodule Jade.Jobs.JobRepo do
  @moduledoc """
  The Repository for Jobs.
  """

  alias Airflow.Dags.Dag
  alias Airflow.Dags.DagRepo

  alias Jade.JobIds.JobIdRepo
  alias Jade.Environments.EnvironmentRepo
  alias Jade.JobRuns.JobRunRepo
  alias Jade.Jobs.Job

  @spec list(map()) :: list(Job.t())
  def list(params) do
    environments = EnvironmentRepo.list(params)

    Enum.reduce(environments, [], fn environment, jobs ->
      result = DagRepo.list(environment, params) |> convert(environment)
      jobs ++ result
    end)
  end

  @spec get(integer(), integer()) :: {:ok, Job.t()} | {:error, :not_found}
  def get(account_id, job_id) do
    with {:ok, job_id} <- JobIdRepo.get_by(id: job_id),
         {:ok, environment} <- EnvironmentRepo.get(account_id, job_id.environment_id),
         {:ok, dag} <- DagRepo.get(environment, job_id.dag_id),
         job <- convert(dag, environment),
         job <- add_most_recent_job_run(environment, job),
         job <- add_most_recent_completed_job_run(environment, job) do
      {:ok, job}
    end
  end

  defp add_most_recent_job_run(environment, job) do
    case JobRunRepo.get_most_recent_for_job(environment, job) do
      {:ok, job_run} -> Map.merge(job, %{most_recent_job_run: job_run})
      _error -> job
    end
  end

  defp add_most_recent_completed_job_run(environment, job) do
    case JobRunRepo.get_most_recent_completed_for_job(environment, job) do
      {:ok, job_run} -> Map.merge(job, %{most_recent_completed_job_run: job_run})
      _error -> job
    end
  end

  defp convert(dags, environment) when is_list(dags) do
    Enum.map(dags, &convert(&1, environment))
  end

  defp convert(%Dag{} = dag, environment) do
    {:ok, job_id} = JobIdRepo.get_or_create_by(environment_id: environment.id, dag_id: dag.dag_id)
    state = if dag.is_active, do: 1, else: 0

    %Job{
      id: job_id.id,
      # Fields needed by BigEye
      project_id: environment.project_id,
      name: dag.dag_id,
      dbt_job_ext_id: job_id.id,
      # -----------------------
      environment_id: environment.id,
      dag_id: dag.dag_id,
      deferring_job_definition_id: nil,
      deferring_environment_id: nil,
      lifecycle_webhooks: nil,
      lifecycle_webhooks_url: nil,
      account_id: environment.account_id,
      description: dag.description,
      # TODO: Parse this from the Manifest once we have it.
      dbt_version: nil,
      # TODO: Parse this from the Manifest once we have it.
      raw_dbt_version: nil,
      triggers: nil,
      created_at: dag.last_parsed_time,
      updated_at: dag.last_parsed_time,
      schedule: dag.schedule_interval,
      settings: nil,
      execution: nil,
      state: state,
      generate_docs: nil,
      run_generate_sources: nil,
      # TODO: Preload most recent runs
      most_recent_completed_run: nil,
      most_recent_run: nil,
      is_deferrable: nil,
      deactivated: !dag.is_active,
      # TODO: Load failed run count
      run_failure_count: nil,
      job_type: nil,
      triggers_on_draft_pr: false
    }
  end
end

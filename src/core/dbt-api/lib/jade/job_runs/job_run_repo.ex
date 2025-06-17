defmodule Jade.JobRuns.JobRunRepo do
  @moduledoc """
  The Repository for JobRuns.
  """

  alias Airflow.DagRuns.DagRun
  alias Airflow.DagRuns.DagRunRepo

  alias Jade.JobIds.JobIdRepo
  alias Jade.JobRunIds.JobRunIdRepo
  alias Jade.Environments.Environment
  alias Jade.Environments.EnvironmentRepo
  alias Jade.JobRuns.JobRun
  alias Jade.Jobs.Job

  @spec list(map()) :: list(JobRun.t())
  def list(params) do
    environments = EnvironmentRepo.list(params)

    Enum.reduce(environments, [], fn environment, job_runs ->
      result = DagRunRepo.list(environment) |> convert(environment)
      job_runs ++ result
    end)
  end

  @spec get(integer(), integer()) :: {:ok, JobRun.t()} | {:error, :not_found}
  def get(account_id, job_run_id) do
    with {:ok, job_run_id} <- JobRunIdRepo.get_by(id: job_run_id),
         {:ok, environment} <- EnvironmentRepo.get(account_id, job_run_id.environment_id),
         {:ok, dag_run} <- DagRunRepo.get(environment, job_run_id.dag_run_id) do
      {:ok, convert(dag_run, environment)}
    end
  end

  def get_by(environment, attrs) do
    with {:ok, dag_run} <- DagRunRepo.get_by(environment, attrs) do
      {:ok, convert(dag_run, environment)}
    end
  end

  @spec get_most_recent_for_job(Environment.t(), Job.t()) ::
          {:ok, JobRun.t()} | {:error, :not_found}
  def get_most_recent_for_job(environment, job) do
    with {:ok, dag_run} <- DagRunRepo.get_most_recent_for_dag(environment, job.dag_id) do
      {:ok, convert(dag_run, environment)}
    end
  end

  @spec get_most_recent_completed_for_job(Environment.t(), Job.t()) ::
          {:ok, JobRun.t()} | {:error, :not_found}
  def get_most_recent_completed_for_job(environment, job) do
    with {:ok, dag_run} <- DagRunRepo.get_most_recent_for_dag(environment, job.dag_id, :success) do
      {:ok, convert(dag_run, environment)}
    end
  end

  @spec get_latest_for_project(map()) :: {:ok, JobRun.t()} | {:error, :not_found}
  def get_latest_for_project(params) do
    environments = EnvironmentRepo.list(params)

    dag_runs =
      Enum.reduce(environments, [], fn environment, dag_runs ->
        case DagRunRepo.get_most_recent(environment, :success) do
          {:ok, dag_run} ->
            [{dag_run, environment} | dag_runs]

          _not_found ->
            dag_runs
        end
      end)

    case dag_runs do
      [] ->
        {:error, :not_found}

      dag_runs ->
        [{latest_dag_run, environment} | _rest] =
          Enum.sort_by(
            dag_runs,
            fn {dag_run, _environment} -> dag_run.end_date end,
            {:desc, DateTime}
          )

        {:ok, convert(latest_dag_run, environment)}
    end
  end

  defp convert(job_runs, environment) when is_list(job_runs) do
    Enum.map(job_runs, &convert(&1, environment))
  end

  defp convert(%DagRun{} = dag_run, environment) do
    {:ok, job_run_id} =
      JobRunIdRepo.get_or_create_by(environment_id: environment.id, dag_run_id: dag_run.id)

    {:ok, job_id} =
      JobIdRepo.get_or_create_by(environment_id: environment.id, dag_id: dag_run.dag_id)

    status = convert_state(dag_run.state)

    %JobRun{
      id: job_run_id.id,
      job_id: job_id.id,
      dag_id: dag_run.dag_id,
      dag_run_id: dag_run.id,
      dag_run_run_id: dag_run.run_id,
      # Fields needed by BigEye
      status: status,
      dbt_job_run_ext_id: dag_run.id,
      started_at: dag_run.start_date,
      completed_at: dag_run.end_date,
      git_sha: nil,
      # ----------------------
      # TODO: Get these fields once we can connect the Environment to DAGs
      trigger_id: nil,
      environment_id: environment.id,
      environment_slug: environment.slug,
      account_id: environment.account_id,
      project_id: environment.project_id,
      git_branch: nil,
      # ------------------
      job_definition_id: dag_run.dag_id,
      status_message: nil,
      owner_thread_id: nil,
      executed_by_thread_id: nil,
      deferring_run_id: nil,
      # TODO: Parse it from the manifest.json
      dbt_version: nil,
      # TODO: Set this to true once we uploaded the manifest to S3
      artifacts_saved: false,
      artifact_s3_path: nil,
      # ----------------------
      has_docs_generated: false,
      has_sources_generated: false,
      notifications_sent: false,
      blocked_by: nil,
      scribe_enabled: nil,
      created_at: dag_run.queued_at,
      updated_at: dag_run.queued_at,
      queued_at: dag_run.queued_at,
      dequeued_at: dag_run.end_date,
      finished_at: dag_run.end_date,
      last_checked_at: nil,
      last_heartbeat_at: nil,
      should_start_at: dag_run.queued_at,
      status_humanized: nil,
      in_progress: dag_run.state == :running,
      is_complete: dag_run.state in [:success, :failed],
      is_success: dag_run.state == :success,
      is_error: dag_run.state == :failed,
      is_cancelled: nil,
      is_running: dag_run.state == :running,
      duration: calc_duration(dag_run.queued_at, dag_run.end_date),
      queued_duration: calc_duration(dag_run.queued_at, dag_run.start_date),
      run_duration: calc_duration(dag_run.start_date, dag_run.end_date),
      duration_humanized: nil,
      queued_duration_humanized: nil,
      run_duration_humanized: nil,
      created_at_humanized: nil,
      finished_at_humanized: nil
    }
  end

  defp convert_state(dag_run_state) do
    case dag_run_state do
      :success -> 1
      :failed -> 2
      :queued -> 3
      :running -> 5
    end
  end

  defp calc_duration(%DateTime{} = start_time, %DateTime{} = end_time) do
    DateTime.diff(end_time, start_time)
  end

  defp calc_duration(_start_time, _end_time), do: nil
end

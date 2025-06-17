defmodule Jade.JobRuns.JobRun do
  @moduledoc """
  The dbt Cloud Job Schema. Its data comes from Airflow DAGRuns.
  """
  use Jade, :schema

  alias Jade.Jobs.Job

  embedded_schema do
    # BigEye internal field. Same as `:id`
    field :dbt_job_run_ext_id, :integer
    belongs_to :job, Job
    field :dag_id, :string
    field :dag_run_id, :integer
    field :dag_run_run_id, :string

    field :trigger_id, :integer
    # has_one :trigger, NotImplemented

    field :environment_id, :integer
    field :environment_slug, :string
    # has_many :run_steps, NotImplemented
    field :account_id, :integer
    field :completed_at, :utc_datetime
    field :project_id, :integer
    field :job_definition_id, :integer
    field :status, :integer
    field :dbt_version, :string, default: "1.6.0-latest"
    field :git_branch, :string
    field :git_sha, :string
    field :status_message, :string
    field :owner_thread_id, :string
    field :executed_by_thread_id, :string
    field :deferring_run_id, :integer
    field :artifacts_saved, :boolean, default: false
    field :artifact_s3_path, :string
    field :has_docs_generated, :boolean, default: false
    field :has_sources_generated, :boolean, default: false
    field :notifications_sent, :boolean, default: false
    field :blocked_by, {:array, :integer}
    field :scribe_enabled, :boolean, default: false
    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime
    field :queued_at, :utc_datetime
    field :dequeued_at, :utc_datetime
    field :started_at, :utc_datetime
    field :finished_at, :utc_datetime
    field :last_checked_at, :utc_datetime
    field :last_heartbeat_at, :utc_datetime
    field :should_start_at, :utc_datetime
    field :status_humanized, :string
    field :in_progress, :boolean
    field :is_complete, :boolean
    field :is_success, :boolean
    field :is_error, :boolean
    field :is_cancelled, :boolean
    field :is_running, :boolean
    field :duration, :string
    field :queued_duration, :string
    field :run_duration, :string
    field :duration_humanized, :string
    field :queued_duration_humanized, :string
    field :run_duration_humanized, :string
    field :created_at_humanized, :string
    field :finished_at_humanized, :string
  end
end

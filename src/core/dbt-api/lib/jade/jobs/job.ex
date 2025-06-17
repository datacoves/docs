defmodule Jade.Jobs.Job do
  @moduledoc """
  The dbt Cloud Job Schema. Its data comes from Airflow DAGs with the exception
  of its integer ID, which we generate as an Jade.JobIds.JobId. The JobId keeps
  the mapping of the generated integer Id to Airflow's string-based ID.
  """
  use Jade, :schema

  alias Jade.JobRuns.JobRun

  @valid_triggers [:github_webhook, :schedule, :git_provider_webhook]

  embedded_schema do
    field :project_id, :integer
    # BigEye internal field. Same as `:id`
    field :dbt_job_ext_id, :integer
    # has_one project, NotImplemented

    field :environment_id, :integer
    # has_one :environment, NotImplemented

    field :dag_id, :string
    field :deferring_job_definition_id, :integer
    field :deferring_environment_id, :integer
    field :lifecycle_webhooks, :boolean
    field :lifecycle_webhooks_url, :string

    field :account_id, :integer
    # has_one :account, NotImplemented

    field :name, :string
    field :description, :string
    field :dbt_version, :string
    field :raw_dbt_version, :string
    field :triggers, Ecto.Enum, values: @valid_triggers
    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime
    field :schedule, :string
    field :settings, :map
    field :execution, :map
    # Valid values not specified in docs.
    field :state, :integer
    field :generate_docs, :boolean
    field :run_generate_sources, :boolean
    field :most_recent_completed_run, :integer
    field :most_recent_run, :integer
    field :is_deferrable, :boolean
    field :deactivated, :boolean
    field :run_failure_count, :integer
    # Valid values not specified in docs.
    field :job_type, :string
    field :triggers_on_draft_pr, :boolean

    has_one :most_recent_job_run, JobRun
    has_one :most_recent_completed_job_run, JobRun
  end

  def valid_triggers(), do: @valid_triggers
end

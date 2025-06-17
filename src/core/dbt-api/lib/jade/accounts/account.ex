defmodule Jade.Accounts.Account do
  @moduledoc """
  The dbt Cloud Account Schema. Its data comes from the Datacoves database.
  """
  use Jade, :schema

  @primary_key false
  embedded_schema do
    field :id, :integer
    field :name, :string
    field :state, :integer
    field :plan, :string
    field :pending_cancel, :boolean
    field :run_slots, :integer
    field :developer_seats, :integer
    field :it_seats, :integer
    field :read_only_seats, :integer
    field :pod_memory_request_mebibytes, :integer
    field :run_duration_limit_seconds, :integer
    field :queue_limit, :integer
    field :stripe_customer_id, :integer
    field :metronome_customer_id, :integer
    field :salesforce_customer_id, :integer
    field :third_party_billing, :boolean
    field :billing_email_address, :string
    field :locked, :boolean
    field :lock_reason, :string
    field :lock_cause, :string
    field :develop_file_system, :boolean
    field :unlocked_at, :utc_datetime
    field :unlock_if_subscription_renewed, :boolean
    field :enterprise_authentication_method, :string
    field :enterprise_login_slug, :string
    field :enterprise_unique_identifier, :string
    field :business_critical, :boolean
    # field :groups, :string <- Add later if needed.
    field :created_at, :utc_datetime
    field :updated_at, :utc_datetime
    field :starter_repo_url, :string
    field :git_auth_level, :string
    field :identifier, :string
    field :trial_end_date, :utc_datetime
    field :static_subdomain, :string
    field :run_locked_until, :utc_datetime
    # Deprecated
    field :docs_job_id, :integer
    # Deprecated
    field :freshness_job_id, :integer
  end
end

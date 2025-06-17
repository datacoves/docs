defmodule Datacoves.Accounts.Account do
  @moduledoc """
  The Account schema as stored in the Datacoves Postgres database.
  """
  use Datacoves, :schema

  schema "users_account" do
    field :approve_billing_events, :boolean
    field :cancelled_subscription, :map
    field :created_at, :utc_datetime
    field :created_by_id, :integer
    field :customer_id, :string
    field :deactivated_at, :utc_datetime
    field :developer_licenses, :integer
    field :name, :string
    field :notifications_enabled, :map
    field :plan_id, :integer
    field :settings, :map
    field :slug, :string
    field :subscription_updated_at, :utc_datetime
    field :subscription, :map
    field :trial_ends_at, :utc_datetime
    field :trial_started_at, :utc_datetime
    field :updated_at, :utc_datetime
    field :workers_execution_limit, :map
  end
end

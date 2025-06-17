defmodule Datacoves.Repo.Migrations.CreateAccounts do
  use Ecto.Migration

  def change do
    create table(:users_account) do
      add :approve_billing_events, :boolean
      add :cancelled_subscription, :map
      add :created_at, :utc_datetime
      add :created_by_id, :integer
      add :customer_id, :string
      add :deactivated_at, :utc_datetime
      add :developer_licenses, :integer
      add :name, :string
      add :notifications_enabled, :map
      add :plan_id, :integer
      add :settings, :map
      add :slug, :string
      add :subscription_updated_at, :utc_datetime
      add :subscription, :map
      add :trial_ends_at, :utc_datetime
      add :trial_started_at, :utc_datetime
      add :updated_at, :utc_datetime
      add :workers_execution_limit, :map
    end
  end
end

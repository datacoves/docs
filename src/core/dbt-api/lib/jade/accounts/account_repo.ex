defmodule Jade.Accounts.AccountRepo do
  @moduledoc """
  The Repository for JobRuns.
  """

  alias Datacoves.Accounts.AccountRepo
  alias Jade.Accounts.Account, as: JadeAccount
  alias Datacoves.Accounts.Account, as: DatacovesAccount

  @spec get(integer()) :: {:ok, JobRun.t()} | {:error, :not_found}
  def get(account_id) do
    with {:ok, datacoves_account} <- AccountRepo.get(account_id) do
      {:ok, convert(datacoves_account)}
    end
  end

  defp convert(accounts) when is_list(accounts) do
    Enum.map(accounts, &convert/1)
  end

  defp convert(%DatacovesAccount{} = account) do
    %JadeAccount{
      id: account.id,
      billing_email_address: nil,
      business_critical: nil,
      created_at: account.created_at,
      develop_file_system: nil,
      developer_seats: account.developer_licenses,
      docs_job_id: nil,
      enterprise_authentication_method: nil,
      enterprise_login_slug: nil,
      enterprise_unique_identifier: nil,
      freshness_job_id: nil,
      git_auth_level: nil,
      identifier: account.slug,
      it_seats: nil,
      lock_cause: nil,
      lock_reason: nil,
      locked: nil,
      metronome_customer_id: nil,
      name: account.name,
      pending_cancel: nil,
      plan: account.plan_id,
      pod_memory_request_mebibytes: nil,
      queue_limit: nil,
      read_only_seats: nil,
      run_duration_limit_seconds: nil,
      run_locked_until: nil,
      run_slots: nil,
      salesforce_customer_id: nil,
      starter_repo_url: nil,
      state: nil,
      static_subdomain: nil,
      stripe_customer_id: nil,
      third_party_billing: nil,
      trial_end_date: account.trial_ends_at,
      unlock_if_subscription_renewed: nil,
      unlocked_at: nil,
      updated_at: account.updated_at
    }
  end
end

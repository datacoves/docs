defmodule JadeWeb.API.V2.AccountControllerTest do
  use JadeWeb.ConnCase, async: true

  defp build_path(account_id) do
    ~p"/api/v2/accounts/#{account_id}"
  end

  setup %{conn: conn} do
    user = insert(:user)
    account = insert(:account)
    auth_token = insert_auth_token_for_user(user, account, nil, nil)
    conn = put_bearer_token(conn, auth_token.key)
    %{conn: conn, account: account, token: auth_token}
  end

  describe "show/2" do
    test "returns a single account", ctx do
      %{data: account} =
        ctx.conn
        |> get(build_path(ctx.account.id))
        |> json_response(200)
        |> assert_schema("ShowAccountResponse", api_spec())

      assert_account_fields(account)
    end

    test "returns an error if an account does not exist", ctx do
      %{errors: %{message: "Invalid Account in Path. You have no accces to this account."}} =
        ctx.conn
        |> get(build_path(404))
        |> json_response(401)
        |> assert_schema("ErrorResponse", api_spec())
    end

    test "returns an error if an account tries to access another account", ctx do
      another_account = insert(:account)

      %{errors: %{message: "Invalid Account in Path. You have no accces to this account."}} =
        ctx.conn
        |> get(build_path(another_account.id))
        |> json_response(401)
        |> assert_schema("ErrorResponse", api_spec())
    end
  end

  defp assert_account_fields(account) do
    assert %{
             id: _id,
             name: _name,
             state: _state,
             plan: _plan,
             pending_cancel: _pending_cancel,
             run_slots: _run_slots,
             developer_seats: _developer_seats,
             it_seats: _it_seats,
             read_only_seats: _read_only_seats,
             pod_memory_request_mebibytes: _pod_memory_request_mebibytes,
             run_duration_limit_seconds: _run_duration_limit_seconds,
             queue_limit: _queue_limit,
             stripe_customer_id: _stripe_customer_id,
             metronome_customer_id: _metronome_customer_id,
             salesforce_customer_id: _salesforce_customer_id,
             third_party_billing: _third_party_billing,
             billing_email_address: _billing_email_address,
             locked: _locked,
             lock_reason: _lock_reason,
             lock_cause: _lock_cause,
             develop_file_system: _develop_file_system,
             unlocked_at: _unlocked_at,
             unlock_if_subscription_renewed: _unlock_if_subscription_renewed,
             enterprise_authentication_method: _enterprise_authentication_method,
             enterprise_login_slug: _enterprise_login_slug,
             enterprise_unique_identifier: _enterprise_unique_identifier,
             business_critical: _business_critical,
             created_at: _created_at,
             updated_at: _updated_at,
             starter_repo_url: _starter_repo_url,
             git_auth_level: _git_auth_level,
             identifier: _identifier,
             trial_end_date: _trial_end_date,
             static_subdomain: _static_subdomain,
             run_locked_until: _run_locked_until,
             docs_job_id: _docs_job_id,
             freshness_job_id: _freshness_job_id
           } = account
  end
end

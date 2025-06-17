defmodule JadeWeb.ManifestControllerTest do
  use JadeWeb.ConnCase, async: true

  defp build_path(account_id, job_run_id) do
    ~p"/api/v2/accounts/#{account_id}/runs/#{job_run_id}/artifacts/manifest.json"
  end

  setup %{conn: conn} do
    user = insert(:user)
    account = insert(:account)
    token = insert_auth_token_for_user(user, account, nil, nil)
    conn = put_bearer_token(conn, token.key)
    %{conn: conn, account: account, token: token}
  end

  describe "show" do
    test "returns the manifest of a job_run", ctx do
      job_run_id = insert(:job_run_id)
      _manifest = insert(:manifest, account_id: ctx.account.id, job_run: job_run_id)

      res_manifest =
        ctx.conn
        |> get(build_path(ctx.account.id, job_run_id.id))
        |> json_response(200)
        |> assert_schema("ShowArtifactResponse", api_spec())

      assert res_manifest.data =~
               "test.balboa.dbt_utils_unique_combination_of_columns_country_populations_country_code__year.f0f4e51143"
    end

    test "returns an error if the manifest belongs to another account", ctx do
      job_run_id = insert(:job_run_id)
      _manifest = insert(:manifest, job_run: job_run_id)

      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account.id, job_run_id.id))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end

    test "returns an error if no manifest exists for the job_run", ctx do
      job_run_id = insert(:job_run_id)

      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account.id, job_run_id.id))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end

    test "returns an error if the job_run does not exist", ctx do
      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account.id, 1))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end
  end
end

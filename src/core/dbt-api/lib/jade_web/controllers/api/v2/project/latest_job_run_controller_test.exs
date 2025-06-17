defmodule JadeWeb.API.V2.Project.LatestJobRunControllerTest do
  use JadeWeb.ConnCase, async: false

  defp build_path(account_id, project_id) do
    "/api/v2/accounts/#{account_id}/projects/#{project_id}/latest-run"
  end

  setup %{conn: conn} do
    attrs = insert_two_accounts_with_repos()
    user = insert(:user)

    token =
      insert_auth_token_for_user(user, attrs.account_1, attrs.environment_1, attrs.project_1)

    conn = put_bearer_token(conn, token.key)

    Map.merge(attrs, %{conn: conn, user: user, token: token})
  end

  describe "show/2" do
    test "returns the latest job run for a project", ctx do
      insert(:dag_run, repo: ctx.repo_1, state: :success, end_date: ~U[2020-01-01 12:00:00Z])

      latest_dag_run =
        insert(:dag_run, repo: ctx.repo_1, state: :success, end_date: ~U[2020-01-02 12:00:00Z])

      # Ignored DagRuns
      insert(:dag_run, repo: ctx.repo_1, state: :success, end_date: nil)
      insert(:dag_run, repo: ctx.repo_1, state: :failed, end_date: ~U[2020-01-01 10:00:00Z])
      insert(:dag_run, repo: ctx.repo_2, state: :success, end_date: ~U[2020-01-01 10:00:00Z])

      %{data: job_run} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, ctx.project_1.id))
        |> json_response(200)
        |> assert_schema("ShowJobRunResponse", api_spec())

      assert job_run.environment_slug == ctx.environment_1.slug
      assert job_run.dag_id == latest_dag_run.dag_id
      assert job_run.dag_run_id == latest_dag_run.id
      assert job_run.dag_run_run_id == latest_dag_run.run_id
      assert job_run.account_id == ctx.account_1.id
      assert job_run.project_id == ctx.project_1.id
    end

    test "returns 404 if no successful dag runs exist", ctx do
      insert(:dag_run, repo: ctx.repo_1, state: :failed, end_date: ~U[2020-01-01 12:00:00Z])
      insert(:dag_run, repo: ctx.repo_1, state: :success, end_date: nil)

      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, ctx.project_1.id))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end
  end
end

defmodule JadeWeb.API.V2.JobRunControllerTest do
  use JadeWeb.ConnCase, async: false

  alias Jade.JobRunIds.JobRunId

  defp build_path(account_id, job_run_id \\ nil) do
    "/api/v2/accounts/#{account_id}/runs" <> "/#{job_run_id}"
  end

  setup %{conn: conn} do
    attrs = insert_two_accounts_with_repos()
    user = insert(:user)

    token =
      insert_auth_token_for_user(user, attrs.account_1, attrs.environment_1, attrs.project_1)

    conn = put_bearer_token(conn, token.key)

    Map.merge(attrs, %{conn: conn, user: user, token: token})
  end

  describe "index/2" do
    test "returns a list of job_runs", ctx do
      dag_run_1 = insert(:dag_run, repo: ctx.repo_1)
      dag_run_2 = insert(:dag_run, repo: ctx.repo_1)
      _ignored_dag_run = insert(:dag_run, repo: ctx.repo_2)

      %{data: data} =
        ctx.conn
        |> get(build_path(ctx.account_1.id))
        |> json_response(200)
        |> assert_schema("ListJobRunsResponse", api_spec())

      assert length(data) == 2

      job_run_ids = Jade.Repo.all(JobRunId)
      assert_lists_equal(data, job_run_ids, &(&1.id == &2.id))

      assert_lists_equal(
        job_run_ids,
        [dag_run_1, dag_run_2],
        &(&1.dag_run_id == &2.id && &1.environment_id == ctx.environment_1.id)
      )
    end

    test "returns an empty list if the account has no job_runs", ctx do
      _ignored_dag = insert(:dag, repo: ctx.repo_2)

      %{data: []} =
        ctx.conn
        |> get(build_path(ctx.account_1.id))
        |> json_response(200)
        |> assert_schema("ListJobRunsResponse", api_spec())
    end

    test "returns an error if the path and token account_id don't match", ctx do
      another_token = insert_auth_token_for_user(insert(:user), ctx.account_2, nil, nil)

      assert %{errors: %{message: message}} =
               ctx.conn
               |> put_bearer_token(another_token.key)
               |> get(build_path(ctx.account_1.id))
               |> json_response(401)
               |> assert_schema("ErrorResponse", api_spec())

      assert message == "Invalid Account in Path. You have no accces to this account."
    end
  end

  describe "show/2" do
    test "returns a single job_run", ctx do
      dag_run = insert(:dag_run, repo: ctx.repo_1)
      _ignored_dag_run = insert(:dag_run, repo: ctx.repo_1)
      _ignored_dag_run = insert(:dag_run, repo: ctx.repo_2)
      _dag_run_with_same_id_in_different_repo = insert(:dag_run, id: dag_run.id, repo: ctx.repo_2)

      job_run_id =
        insert(:job_run_id, environment_id: ctx.environment_1.id, dag_run_id: dag_run.id)

      %{data: job_run} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, job_run_id.id))
        |> json_response(200)
        |> assert_schema("ShowJobRunResponse", api_spec())

      assert job_run.id == job_run_id.id
    end

    test "returns an error if a job_run does not exist", ctx do
      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, 404))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end
  end
end

defmodule JadeWeb.API.V2.JobControllerTest do
  use JadeWeb.ConnCase, async: false

  alias Jade.JobIds.JobIdRepo

  defp build_path(account_id, job_id \\ nil) do
    ~p"/api/v2/accounts/#{account_id}/jobs" <> "/#{job_id}"
  end

  setup %{conn: conn} do
    attrs = insert_two_accounts_with_repos()
    user = insert(:user)

    token = insert_auth_token_for_user(user, attrs.account_1, nil, nil)
    conn = put_bearer_token(conn, token.key)

    Map.merge(attrs, %{conn: conn, user: user, token: token})
  end

  describe "index/2" do
    test "returns a list of jobs and creates integer IDs for them", ctx do
      dag_1 = insert(:dag, repo: ctx.repo_1)
      dag_2 = insert(:dag, repo: ctx.repo_1)
      _ignored_dag = insert(:dag, repo: ctx.repo_2)

      %{data: data} =
        ctx.conn
        |> get(build_path(ctx.account_1.id))
        |> json_response(200)
        |> assert_schema("ListJobsResponse", api_spec())

      assert length(data) == 2
      assert_lists_equal(data, [dag_1, dag_2], &(&1.name == &2.dag_id))

      job_ids = JobIdRepo.list()
      assert_lists_equal(data, job_ids, &(&1.id == &2.id))
      assert_lists_equal(data, job_ids, &(&1.name == &2.dag_id))
    end

    test "returns an empty list if the account has no jobs", ctx do
      _ignored_dag = insert(:dag, repo: ctx.repo_2)

      %{data: []} =
        ctx.conn
        |> get(build_path(ctx.account_1.id))
        |> json_response(200)
        |> assert_schema("ListJobsResponse", api_spec())
    end

    test "returns an error if the path and token account_id don't match", ctx do
      another_token = insert_auth_token_for_user(insert(:user), ctx.account_2, nil, nil)

      assert %{errors: %{message: "Invalid Account in Path. You have no accces to this account."}} =
               ctx.conn
               |> put_bearer_token(another_token.key)
               |> get(build_path(ctx.account_1.id))
               |> json_response(401)
               |> assert_schema("ErrorResponse", api_spec())
    end
  end

  describe "show/2" do
    test "returns a single job", ctx do
      dag = insert(:dag, repo: ctx.repo_1)
      _ignored_dag = insert(:dag, repo: ctx.repo_1)
      _ignored_dag = insert(:dag, repo: ctx.repo_2)
      _dag_with_same_id_in_different_repo = insert(:dag, dag_id: dag.dag_id, repo: ctx.repo_2)
      job_id = insert(:job_id, environment_id: ctx.environment_1.id, dag_id: dag.dag_id)

      %{data: job} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, job_id.id))
        |> json_response(200)
        |> assert_schema("ShowJobResponse", api_spec())

      assert job.id == job_id.id
      assert job.dag_id == dag.dag_id
      assert job.dag_id == job_id.dag_id
    end

    test "loads the most recent job_run and most recent completed job_run", ctx do
      dag = insert(:dag, repo: ctx.repo_1)
      job_id = insert(:job_id, environment_id: ctx.environment_1.id, dag_id: dag.dag_id)

      most_recent_job_run =
        insert(:dag_run,
          dag_id: dag.dag_id,
          state: :failed,
          end_date: ~U[2023-01-01 12:00:00Z],
          repo: ctx.repo_1
        )

      most_recent_completed_job_run =
        insert(:dag_run,
          dag_id: dag.dag_id,
          state: :success,
          end_date: ~U[2023-01-01 11:00:00Z],
          repo: ctx.repo_1
        )

      _older_job_run =
        insert(:dag_run, dag_id: dag.dag_id, end_date: ~U[2023-01-01 10:00:00Z], repo: ctx.repo_1)

      %{data: job} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, job_id.id))
        |> json_response(200)
        |> assert_schema("ShowJobResponse", api_spec())

      assert job.most_recent_job_run.dag_run_id == most_recent_job_run.id

      assert job.most_recent_completed_job_run.dag_run_id ==
               most_recent_completed_job_run.id
    end

    test "returns an error if a Job hasn't been fetched earlier and we don't have an ID -> JobId mapping",
         ctx do
      insert(:dag, repo: ctx.repo_1)

      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, 1))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end

    test "returns an error if the job belongs to another account", ctx do
      dag = insert(:dag, repo: ctx.repo_2)
      job_id = insert(:job_id, environment_id: ctx.environment_2.id, dag_id: dag.dag_id)

      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, job_id.id))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end

    test "returns an error if a job does not exist", ctx do
      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account_1.id, 404))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end
  end
end

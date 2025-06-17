defmodule JadeWeb.API.V2.EnvironmentControllerTest do
  use JadeWeb.ConnCase, async: true

  defp build_path(account_id, environment_id \\ nil) do
    ~p"/api/v2/accounts/#{account_id}/environments" <> "/#{environment_id}"
  end

  setup %{conn: conn} do
    user = insert(:user)
    account = insert(:account)
    project = insert(:project, account: account)

    token = insert_auth_token_for_user(user, account, nil, project)
    conn = put_bearer_token(conn, token.key)
    %{conn: conn, account: account, project: project, token: token}
  end

  describe "index/2" do
    test "returns a list of environments", ctx do
      insert_pair(:environment, project: ctx.project)

      %{data: data} =
        ctx.conn
        |> get(build_path(ctx.account.id))
        |> json_response(200)
        |> assert_schema("ListEnvironmentsResponse", api_spec())

      assert length(data) == 2
    end

    test "returns an error if the path and token account_id don't match", ctx do
      insert_pair(:environment, project: ctx.project)
      another_account = insert(:account)
      another_token = insert_auth_token_for_user(insert(:user), another_account, nil, nil)

      assert %{errors: %{message: message}} =
               ctx.conn
               |> put_bearer_token(another_token.key)
               |> get(build_path(ctx.account.id))
               |> json_response(401)
               |> assert_schema("ErrorResponse", api_spec())

      assert message == "Invalid Account in Path. You have no accces to this account."
    end

    test "paginates the response", ctx do
      insert_list(3, :environment, project: ctx.project)
      params = %{limit: 2, offset: 2}

      %{data: data} =
        ctx.conn
        |> get(build_path(ctx.account.id), params)
        |> json_response(200)
        |> assert_schema("ListEnvironmentsResponse", api_spec())

      assert length(data) == 1
    end
  end

  describe "show/2" do
    test "returns a single environment", ctx do
      environment = insert(:environment, project: ctx.project)

      %{data: res_environment} =
        ctx.conn
        |> get(build_path(ctx.account.id, environment.id))
        |> json_response(200)
        |> assert_schema("ShowEnvironmentResponse", api_spec())

      assert res_environment.id == environment.id
    end

    test "returns an error if the environment belongs to another account", ctx do
      environment = insert(:environment)

      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account.id, environment.id))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end

    test "returns an error if a environment does not exist", ctx do
      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account.id, 404))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end
  end
end

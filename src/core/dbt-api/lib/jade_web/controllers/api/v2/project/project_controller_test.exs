defmodule JadeWeb.API.V2.ProjectControllerTest do
  use JadeWeb.ConnCase, async: true

  defp build_path(account_id, project_id \\ nil) do
    ~p"/api/v2/accounts/#{account_id}/projects" <> "/#{project_id}"
  end

  setup %{conn: conn} do
    user = insert(:user)
    account = insert(:account)
    token = insert_auth_token_for_user(user, account, nil, nil)
    conn = put_bearer_token(conn, token.key)
    %{conn: conn, user: user, account: account, token: token}
  end

  describe "index/2" do
    test "returns a list of projects", ctx do
      insert_pair(:project, account: ctx.account)

      %{data: data} =
        ctx.conn
        |> get(build_path(ctx.account.id))
        |> json_response(200)
        |> assert_schema("ListProjectsResponse", api_spec())

      assert length(data) == 2
    end

    test "returns an error if the path and token account_id don't match", ctx do
      insert_pair(:project, account: ctx.account)
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
      insert_list(3, :project, account: ctx.account)
      params = %{limit: 2, offset: 2}

      %{data: data} =
        ctx.conn
        |> get(build_path(ctx.account.id), params)
        |> json_response(200)
        |> assert_schema("ListProjectsResponse", api_spec())

      assert length(data) == 1
    end
  end

  describe "show/2" do
    test "returns a single project", ctx do
      project = insert(:project, account: ctx.account)

      %{data: res_project} =
        ctx.conn
        |> get(build_path(ctx.account.id, project.id))
        |> json_response(200)
        |> assert_schema("ShowProjectResponse", api_spec())

      assert res_project.id == project.id
    end

    test "returns an error if the project belongs to another account", ctx do
      another_account = insert(:account)
      project = insert(:project, account: another_account)

      %{errors: %{message: "Not Found"}} =
        ctx.conn
        |> get(build_path(ctx.account.id, project.id))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end

    test "returns an error if a project does not exist", ctx do
      %{
        errors: %{
          message: "Not Found"
        }
      } =
        ctx.conn
        |> get(build_path(ctx.account.id, 404))
        |> json_response(404)
        |> assert_schema("ErrorResponse", api_spec())
    end
  end
end

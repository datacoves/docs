defmodule JadeWeb.Plugs.AuthenticateApiKeyTest do
  use JadeWeb.ConnCase, async: true

  alias JadeWeb.Plugs.AuthenticateApiKey

  import ExUnit.CaptureLog

  setup do
    user = insert(:user, is_service_account: true)
    environment = insert(:environment, slug: "env123")
    auth_token = insert_auth_token_for_user(user, nil, environment, nil)

    %{user: user, auth_token: auth_token}
  end

  test "allows a conn with valid bearer token to pass", %{auth_token: auth_token} do
    conn =
      build_conn(:get, ~p"/api/v2/datacoves/manifests", %{"environment_slug" => "env123"})
      |> put_bearer_token(auth_token.key)
      |> AuthenticateApiKey.call([])

    refute conn.halted
  end

  test "halts if the user of the bearer token has no permissions at all" do
    user = insert(:user, is_service_account: true)
    auth_token = insert(:auth_token, user: user)

    conn =
      build_conn(:get, ~p"/api/v2/datacoves/manifests", %{"environment_slug" => "env123"})
      |> put_bearer_token(auth_token.key)
      |> AuthenticateApiKey.call([])

    assert conn.halted
  end

  test "halts if the user of the bearer token has no matching permission" do
    user = insert(:user, is_service_account: true)
    auth_token = insert(:auth_token, user: user)

    conn =
      build_conn(:get, ~p"/api/v2/datacoves/manifests", %{"environment_slug" => "env123"})
      |> put_bearer_token(auth_token.key)
      |> AuthenticateApiKey.call([])

    assert conn.halted
  end

  test "halts the conn and writes a log if an invalid internal bearer token was given", %{
    conn: conn
  } do
    assert capture_log(fn ->
             conn =
               conn
               |> put_bearer_token("invalid-token")
               |> AuthenticateApiKey.call([])

             assert conn.halted

             assert %{"errors" => %{"message" => message}} = Jason.decode!(conn.resp_body)
             assert message == "Invalid API Key. Please use a valid Bearer Token."
           end) =~ "Verifying ApiKey returned 401 with \"Invalid token\""
  end

  test "halts the conn if no bearer token was given", %{conn: conn} do
    conn = AuthenticateApiKey.call(conn, [])
    assert conn.halted
  end

  test "halts the conn if no path arameter was given", %{conn: conn} do
    user = insert(:user, is_service_account: true)
    auth_token = insert(:auth_token, user: user)

    assert capture_log(fn ->
             conn = conn |> put_bearer_token(auth_token.key) |> AuthenticateApiKey.call([])
             assert conn.halted
           end) =~ "AuthenticateApiKey missed a path parameter or api key details"
  end
end

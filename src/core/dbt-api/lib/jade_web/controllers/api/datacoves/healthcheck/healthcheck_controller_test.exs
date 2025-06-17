defmodule JadeWeb.API.Datacoves.HealthcheckControllerTest do
  use JadeWeb.ConnCase, async: true

  test "returns 200 for the /api/v2 scope", %{conn: conn} do
    conn = get(conn, ~p"/api/v2/healthcheck")
    assert conn.status == 200
    assert conn.resp_body == "ok"
  end

  test "returns 200 for the /api/internal scope", %{conn: conn} do
    conn = get(conn, ~p"/api/internal/healthcheck")
    assert conn.status == 200
    assert conn.resp_body == "ok"
  end
end

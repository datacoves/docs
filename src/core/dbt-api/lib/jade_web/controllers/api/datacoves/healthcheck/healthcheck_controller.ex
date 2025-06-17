defmodule JadeWeb.API.Datacoves.HealthcheckController do
  use JadeWeb, :controller

  tags ["datacoves"]

  operation(:show,
    summary: "Returns 'ok' if the application if online.",
    responses: [
      ok: Generic.ok()
    ]
  )

  def show(conn, _params), do: send_resp(conn, 200, "ok")
end

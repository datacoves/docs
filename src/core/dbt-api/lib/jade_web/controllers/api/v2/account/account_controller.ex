defmodule JadeWeb.API.V2.AccountController do
  use JadeWeb, :controller

  alias Jade.Accounts.AccountRepo

  plug OpenApiSpex.Plug.CastAndValidate, json_render_error_v2: true

  tags ["dbt-api"]

  operation(:show,
    summary: "Shows a single account.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1]
    ],
    responses: [
      ok: Generic.response(Schemas.ShowAccountResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{account_id: account_id}) do
    with {:ok, account} <- AccountRepo.get(account_id) do
      render(conn, :show, account: account)
    end
  end
end

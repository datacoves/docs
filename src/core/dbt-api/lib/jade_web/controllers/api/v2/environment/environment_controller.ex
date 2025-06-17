defmodule JadeWeb.API.V2.EnvironmentController do
  use JadeWeb, :controller

  alias Jade.Environments.EnvironmentRepo

  plug OpenApiSpex.Plug.CastAndValidate, json_render_error_v2: true

  tags ["dbt-api"]

  operation(:index,
    summary: "List all environments of an account.",
    parameters: [
      account_id: [in: :path, description: "Environment ID", type: :integer, example: 1],
      limit: Pagination.limit(),
      offset: Pagination.offset()
    ],
    responses: [
      ok: Generic.response(Schemas.ListEnvironmentsResponse),
      unauthorized: Generic.unauthorized()
    ]
  )

  def index(conn, params) do
    environments = EnvironmentRepo.list(params)
    render(conn, :index, environments: environments)
  end

  operation(:show,
    summary: "Shows a single environment.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1],
      id: [in: :path, description: "Environment ID", type: :integer, example: 1]
    ],
    responses: [
      ok: Generic.response(Schemas.ShowEnvironmentResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{id: environment_id, account_id: account_id}) do
    with {:ok, environment} <- EnvironmentRepo.get(account_id, environment_id) do
      render(conn, :show, environment: environment)
    end
  end
end

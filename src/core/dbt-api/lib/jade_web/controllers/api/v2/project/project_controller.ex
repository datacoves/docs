defmodule JadeWeb.API.V2.ProjectController do
  use JadeWeb, :controller

  alias Jade.Projects.ProjectRepo

  plug OpenApiSpex.Plug.CastAndValidate, json_render_error_v2: true

  tags ["dbt-api"]

  operation(:index,
    summary: "List all projects of an account.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1],
      limit: Pagination.limit(),
      offset: Pagination.offset()
    ],
    responses: [
      ok: Generic.response(Schemas.ListProjectsResponse),
      unauthorized: Generic.unauthorized()
    ]
  )

  def index(conn, params) do
    projects = ProjectRepo.list(params)
    render(conn, :index, projects: projects)
  end

  operation(:show,
    summary: "Show a single project of an account.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1],
      id: [in: :path, description: "Project ID", type: :integer, example: 1]
    ],
    responses: [
      ok: Generic.response(Schemas.ShowProjectResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{id: project_id, account_id: account_id}) do
    with {:ok, project} <- ProjectRepo.get_by(id: project_id, account_id: account_id) do
      render(conn, :show, project: project)
    end
  end
end

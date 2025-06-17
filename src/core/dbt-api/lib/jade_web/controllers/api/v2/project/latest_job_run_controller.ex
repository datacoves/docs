defmodule JadeWeb.API.V2.Project.LatestJobRunController do
  use JadeWeb, :controller

  alias Jade.JobRuns.JobRunRepo

  plug OpenApiSpex.Plug.CastAndValidate, json_render_error_v2: true

  tags ["dbt-api"]

  operation(:show,
    summary: "Show the latest, successful job run of a project.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1],
      project_id: [in: :path, description: "Project ID", type: :integer, example: 1]
    ],
    responses: [
      ok: Generic.response(Schemas.ShowJobRunResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, params) do
    with {:ok, job_run} <- JobRunRepo.get_latest_for_project(params) do
      render(conn, :show, job_run: job_run)
    end
  end
end

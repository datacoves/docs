defmodule JadeWeb.API.V2.JobController do
  use JadeWeb, :controller

  alias Jade.Jobs.JobRepo

  plug OpenApiSpex.Plug.CastAndValidate, json_render_error_v2: true

  tags ["dbt-api"]

  operation(:index,
    summary: "List all jobs of an account.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1]
    ],
    responses: [
      ok: Generic.response(Schemas.ListJobsResponse),
      unauthorized: Generic.unauthorized()
    ]
  )

  def index(conn, params) do
    jobs = JobRepo.list(params)
    render(conn, :index, jobs: jobs)
  end

  operation(:show,
    summary: "Show a single job of an account.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1],
      id: [in: :path, description: "Job ID", type: :string, example: "sample_project_1"]
    ],
    responses: [
      ok: Generic.response(Schemas.ShowJobResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{id: job_id, account_id: account_id}) do
    with {:ok, job} <- JobRepo.get(account_id, job_id) do
      render(conn, :show, job: job)
    end
  end
end

defmodule JadeWeb.API.V2.JobRunController do
  use JadeWeb, :controller

  alias Jade.JobRuns.JobRunRepo

  plug OpenApiSpex.Plug.CastAndValidate, json_render_error_v2: true

  tags ["dbt-api"]

  operation(:index,
    summary: "List all jobs of an account.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1]
    ],
    responses: %{
      200 => Generic.response(Schemas.ListJobRunsResponse),
      401 => Generic.not_found()
    }
  )

  def index(conn, params) do
    job_runs = JobRunRepo.list(params)
    render(conn, :index, job_runs: job_runs)
  end

  operation(:show,
    summary: "Show a single job of an account.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1],
      id: [in: :path, description: "Job ID", type: :integer, example: 1]
    ],
    responses: [
      ok: Generic.response(Schemas.ShowJobRunResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{id: job_run_id, account_id: account_id}) do
    with {:ok, job_run} <- JobRunRepo.get(account_id, job_run_id) do
      render(conn, :show, job_run: job_run)
    end
  end
end

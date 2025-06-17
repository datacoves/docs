defmodule JadeWeb.API.V2.ManifestController do
  use JadeWeb, :controller

  alias Jade.Manifests.ManifestRepo

  plug OpenApiSpex.Plug.CastAndValidate, json_render_error_v2: true

  tags ["dbt-api"]

  operation(:show,
    summary: "Return an artifact for a JobRun.",
    parameters: [
      account_id: [in: :path, description: "Account ID", type: :integer, example: 1],
      job_run_id: [in: :path, description: "JobRun ID", type: :integer, example: 1],
      artifact: [in: :path, description: "Artifact type", type: :string, example: "manifest.json"]
    ],
    responses: [
      ok: Generic.response(Schemas.ShowArtifactResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{account_id: account_id, job_run_id: job_run_id, artifact: "manifest.json"}) do
    with {:ok, manifest} <- ManifestRepo.get_by(account_id: account_id, job_run_id: job_run_id),
         {:ok, file} <- ManifestRepo.download_file(manifest) do
      render(conn, file: file)
    end
  end
end

defmodule JadeWeb.API.Datacoves.ProjectManifestController do
  use JadeWeb, :controller

  alias Jade.Manifests.ManifestRepo
  alias Jade.Projects.ProjectRepo

  require Logger

  tags ["datacoves"]

  operation(:show,
    summary: "Shows the latest Manifest for a Project.",
    parameters: [
      project_slug: [
        in: :path,
        description: "Project Slug",
        type: :string
      ],
      trimmed: [in: :query, description: "Get trimmed manifest", type: :boolean]
    ],
    responses: [
      ok: Generic.response(Schemas.FileContent),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{"project_slug" => project_slug} = params) do
    with {:ok, project} <- ProjectRepo.get_by(slug: project_slug),
         {:ok, manifest} <- ManifestRepo.get_latest_for_project(project),
         content <- get_manifest(manifest, params) do
      conn
      |> put_status(:ok)
      |> json(content)
    end
  end

  defp get_manifest(manifest, %{"trimmed" => trimmed}) when trimmed in [false, "false"] do
    ManifestRepo.get_full_content(manifest)
  end

  defp get_manifest(manifest, _params) do
    ManifestRepo.get_minimal_content(manifest)
  end
end

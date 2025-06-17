defmodule JadeWeb.API.Datacoves.ManifestController do
  use JadeWeb, :controller

  alias Jade.Environments.EnvironmentRepo
  alias Jade.Manifests.ManifestRepo

  require Logger

  tags ["datacoves"]

  operation(:create,
    summary: "Create a manifest for a given environment.",
    parameters: [
      environment_slug: [
        in: :path,
        description: "Environment Slug",
        type: :string,
        example: "env123"
      ],
      dag_id: [in: :query, description: "Dag ID", type: :string, example: "sample_dag"],
      run_id: [
        in: :query,
        description: "Dag Run Run ID",
        type: :string,
        example: "manual__2023-12-02T09:49:46.105347+00:00"
      ]
    ],
    request_body: {"File Upload", "multipart/form-data", Schemas.FileUpload, required: true},
    responses: [
      ok: Generic.response(Schemas.FileOrFilesResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def create(
        conn,
        %{
          "file" => upload,
          "dag_id" => dag_id,
          "run_id" => run_id,
          "environment_slug" => environment_slug
        } = params
      ) do
    tag = Map.get(params, "tag")

    with {:ok, content} <- File.read(upload.path),
         {:ok, _manifest} <- ManifestRepo.create(environment_slug, dag_id, run_id, content, tag) do
      conn
      |> put_status(:created)
      |> json(:ok)
    end
  end

  def create(conn, %{"file" => upload, "environment_slug" => environment_slug} = params) do
    tag = Map.get(params, "tag")

    with {:ok, content} <- File.read(upload.path),
         {:ok, _manifest} <- ManifestRepo.create(environment_slug, content, tag) do
      conn
      |> put_status(:created)
      |> json(:ok)
    end
  end

  operation(:show,
    summary: "Shows a single manifest.",
    parameters: [
      environment_slug: [
        in: :path,
        description: "Environment Slug",
        type: :string,
        example: "env123"
      ],
      dag_id: [in: :query, description: "Dag ID", type: :string, example: "sample_dag"],
      tag: [in: :query, description: "Manifest tag", type: :string],
      trimmed: [in: :query, description: "Get trimmed manifest", type: :boolean]
    ],
    responses: [
      ok: Generic.response(Schemas.FileContent),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{"dag_id" => dag_id} = params) do
    with {:ok, manifest} <- ManifestRepo.get_by(dag_id: dag_id),
         content <- get_manifest(manifest, params) do
      conn
      |> put_status(:ok)
      |> json(content)
    end
  end

  def show(conn, %{"environment_slug" => environment_slug, "tag" => tag} = params) do
    with {:ok, environment} <- EnvironmentRepo.get_by_slug(environment_slug),
         {:ok, manifest} <- ManifestRepo.get_by(environment_slug: environment.slug, tag: tag),
         content <- get_manifest(manifest, params) do
      conn
      |> put_status(:ok)
      |> json(content)
    end
  end

  def show(conn, %{"environment_slug" => environment_slug} = params) do
    with {:ok, environment} <- EnvironmentRepo.get_by_slug(environment_slug),
         {:ok, manifest} <- ManifestRepo.get_latest_for_environment(environment),
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

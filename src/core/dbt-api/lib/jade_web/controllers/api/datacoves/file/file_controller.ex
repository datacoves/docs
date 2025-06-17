defmodule JadeWeb.API.Datacoves.FileController do
  use JadeWeb, :controller

  alias Jade.Files.FileRepo

  tags ["datacoves"]

  operation(:create,
    summary: "Create one or multiple files for a given environment.",
    parameters: [
      environment_slug: [
        in: :path,
        description: "Environment Slug",
        type: :string,
        example: "env123"
      ]
    ],
    request_body:
      {"File Upload", "multipart/form-data", Schemas.OneOrMultipleFileUploads, required: true},
    responses: [
      ok: Generic.response(Schemas.FileOrFilesResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def create(conn, %{"file" => %Plug.Upload{} = upload} = params) do
    params =
      Map.merge(params, %{"filename" => upload.filename, "contents" => File.read!(upload.path)})

    with {:ok, file} <- FileRepo.create_file(params) do
      conn
      |> put_resp_header(
        "location",
        ~p"/api/v2/datacoves/environments/#{file.environment_slug}/files/?#{[slug: file.slug]}"
      )
      |> put_status(:created)
      |> render(:show, file: file)
    end
  end

  def create(conn, %{"environment_slug" => environment_slug, "files" => files})
      when is_map(files) do
    files =
      Enum.map(files, fn {_idx, %{"file" => %Plug.Upload{} = upload} = file_params} ->
        Map.merge(file_params, %{
          "environment_slug" => environment_slug,
          "filename" => upload.filename,
          "contents" => File.read!(upload.path)
        })
      end)

    with {:ok, files} <- FileRepo.create_files(files) do
      conn
      |> put_status(:created)
      |> render(:index, files: files)
    end
  end

  operation(:show,
    summary: "Shows a single file.",
    parameters: [
      environment_slug: [
        in: :path,
        description: "Environment Slug",
        type: :string,
        required: true,
        example: "env123"
      ],
      slug: [in: :query, description: "File slug", type: :string, required: false],
      tag: [in: :query, description: "File tag", type: :string, required: false],
      filename: [in: :query, description: "File filename", type: :string, required: false]
    ],
    responses: [
      ok: Generic.response(Schemas.FileResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def show(conn, %{"environment_slug" => environment_slug, "slug" => slug}) when slug != "" do
    with {:ok, file} <-
           FileRepo.get_and_download_file_by(environment_slug: environment_slug, slug: slug) do
      render(conn, :show, file: file)
    end
  end

  def show(conn, %{"environment_slug" => environment_slug, "tag" => tag}) when tag != "" do
    with {:ok, file} <-
           FileRepo.get_and_download_file_by(environment_slug: environment_slug, tag: tag) do
      render(conn, :show, file: file)
    end
  end

  def show(conn, %{"environment_slug" => environment_slug, "filename" => filename})
      when filename != "" do
    attrs = %{environment_slug: environment_slug, filename: filename}

    with {:ok, file} <- FileRepo.get_and_download_file_by(attrs) do
      render(conn, :show, file: file)
    end
  end

  operation(:update,
    summary: "Updates a file.",
    parameters: [
      environment_slug: [
        in: :path,
        description: "Environment Slug",
        type: :string,
        example: "env123"
      ],
      slug: [
        in: :query,
        description: "A File slug. Supersedes the tag.",
        type: :string,
        required: false
      ],
      tag: [in: :query, description: "A File tag", type: :string, required: false]
    ],
    request_body: {"File Upload", "multipart/form-data", Schemas.FileUpload, required: true},
    responses: [
      ok: Generic.response(Schemas.FileResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def update(conn, %{"environment_slug" => environment_slug, "slug" => slug} = params)
      when slug != "" do
    with {:ok, file} <- FileRepo.get_file_by(slug: slug, environment_slug: environment_slug) do
      do_update(conn, file, params)
    end
  end

  def update(conn, %{"environment_slug" => environment_slug, "tag" => tag} = params)
      when tag != "" do
    with {:ok, file} <- FileRepo.get_file_by(tag: tag, environment_slug: environment_slug) do
      do_update(conn, file, params)
    end
  end

  defp do_update(conn, file, %{"file" => %Plug.Upload{} = upload} = params) do
    with {:ok, contents} <- File.read(upload.path),
         params <- Map.merge(params, %{"contents" => contents, "filename" => upload.filename}),
         {:ok, file} <- FileRepo.update_file(file, params) do
      render(conn, :show, file: file)
    end
  end

  operation(:delete,
    summary: "Deletes a file.",
    parameters: [
      environment_slug: [
        in: :path,
        description: "Environment Slug",
        type: :string,
        example: "env123"
      ],
      slug: [
        in: :query,
        description: "A File slug. Supersedes the tag.",
        type: :string,
        required: false
      ],
      tag: [in: :query, description: "A File tag", type: :string, required: false]
    ],
    responses: [
      ok: Generic.response(Schemas.SuccessResponse),
      unauthorized: Generic.unauthorized(),
      not_found: Generic.not_found()
    ]
  )

  def delete(conn, %{"environment_slug" => environment_slug, "slug" => slug} = _params)
      when slug != "" do
    with {:ok, file} <- FileRepo.get_file_by(slug: slug, environment_slug: environment_slug),
         {:ok, _file} <- FileRepo.delete_file(file) do
      send_resp(conn, 200, "")
    end
  end

  def delete(conn, %{"environment_slug" => environment_slug, "tag" => tag} = _params)
      when tag != "" do
    with {:ok, file} <- FileRepo.get_file_by(tag: tag, environment_slug: environment_slug),
         {:ok, _file} <- FileRepo.delete_file(file) do
      send_resp(conn, 200, "")
    end
  end
end

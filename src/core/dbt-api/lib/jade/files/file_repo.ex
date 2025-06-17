defmodule Jade.Files.FileRepo do
  @moduledoc """
  The repository for Files.
  """

  use Jade, :repository
  require Logger
  import Ecto.Query

  alias Jade.Files.File
  alias Jade.Storage

  @doc """
  Get a file by its slug.
  """
  def get_file!(slug), do: Repo.get!(File, slug)

  @doc """
  Get file by its attributes.
  """
  def get_file_by(attrs) do
    query = from(f in File)

    query =
      attrs
      |> Enum.reduce(query, fn {k, v}, query -> where(query, [f], field(f, ^k) == ^v) end)
      |> order_by([f], desc: f.inserted_at)
      |> limit(1)

    query
    |> Repo.all()
    |> Repo.normalize_one()
  end

  @doc """
  Gets files by its attributes.
  """
  def get_files_by(attrs) do
    query = from(f in File)

    query =
      attrs
      |> Enum.reduce(query, fn {k, v}, query -> where(query, [f], field(f, ^k) == ^v) end)
      |> order_by([f], desc: f.inserted_at)

    query
    |> Repo.all()
    |> Repo.normalize_all()
  end

  @doc """
  Get and download a file by its attributes.
  """
  def get_and_download_file_by(attrs) do
    with {:ok, file} <- get_file_by(attrs) do
      download_file(file)
    end
  end

  @doc """
  Creates file and uploads them to storage
  """
  def create_file(attrs \\ %{}) do
    Ecto.Multi.new()
    |> Ecto.Multi.run(:file, fn _repo, _changes -> do_create_file(attrs) end)
    |> Ecto.Multi.run(:upload, fn _repo, %{file: file} ->
      case upload_file(file) do
        :ok -> {:ok, file}
        {:error, _status, reason} -> {:error, reason}
      end
    end)
    |> Repo.transaction()
    |> case do
      {:ok, %{file: file}} ->
        {:ok, file}

      {:error, :file, changeset, _} ->
        {:error, changeset}

      {:error, :upload, _reason, _} ->
        {:error, :unprocessable_entity, "File upload failed. Please check the error in the logs."}
    end
  end

  @doc """
  Creates multiple files and uploads them to storage
  """
  def create_files(files) do
    files
    |> Enum.reduce_while([], fn file_params, acc ->
      case create_file(file_params) do
        {:ok, file} ->
          {:cont, [file | acc]}

        error ->
          Logger.error("Creating multiple files failed: #{inspect(error)}")
          delete_files(acc)
          {:halt, error}
      end
    end)
    |> case do
      {:error, _msg} = error -> error
      {:error, _status, reason} -> {:error, reason}
      files -> {:ok, Enum.reverse(files)}
    end
  end

  defp do_create_file(attrs) do
    %File{}
    |> File.changeset(attrs)
    |> Repo.insert()
  end

  @doc """
  Updates a file and uploads it to storage
  """
  def update_file(file, attrs \\ %{}) do
    Ecto.Multi.new()
    |> Ecto.Multi.run(:file, fn _repo, _changes -> do_update_file(file, attrs) end)
    |> Ecto.Multi.run(:upload, fn _repo, %{file: file} ->
      case upload_file(file) do
        :ok -> {:ok, file}
        {:error, _status, reason} -> {:error, reason}
      end
    end)
    |> Repo.transaction()
    |> case do
      {:ok, %{file: file}} ->
        {:ok, file}

      {:error, :file, changeset, _} ->
        {:error, changeset}

      {:error, :upload, _reason, _} ->
        {:error, :unprocessable_entity, "File upload failed. Please check the error in the logs."}
    end
  end

  defp do_update_file(file, attrs) do
    file
    |> File.changeset(attrs)
    |> Repo.update()
  end

  @doc """
  Deletes a file and its contents from storage
  """
  def delete_file(%File{} = file) do
    case Storage.delete(file.path) do
      :ok ->
        Repo.delete(file)

      {:error, :http_request_failed} ->
        {:error, :unprocessable_entity,
         "Deletion of file contents from storage failed. File record and contents remain."}
    end
  end

  def delete_files(files) do
    Enum.each(files, &delete_file/1)
  end

  defp upload_file(file) do
    case Storage.upload(file.path, file.contents) do
      :ok ->
        :ok

      {:error, :http_request_failed} ->
        delete_file(file)
        {:error, :unprocessable_entity, "File upload failed. Please check the error in the logs."}
    end
  end

  defp download_file(file) do
    case Storage.download(file.path) do
      {:ok, contents} ->
        {:ok, Map.put(file, :contents, contents)}

      {:error, :not_found} ->
        {:error, :not_found, "File found but could not download contents from storage bucket."}

      {:error, :http_request_failed} ->
        {:error, :unprocessable_entity, "The request to the storage bucket failed."}
    end
  end
end

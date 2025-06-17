defmodule Jade.Storage.Minio do
  @moduledoc """
  The Storage Adapter for Minio used in local development.
  """

  @behaviour Jade.Storage.Adapter
  @http_adapter Application.compile_env(:jade, :http_adapter)

  @impl true
  def upload(bucket, filename, contents) do
    with {:ok, url} <- get_upload_url(bucket, filename) do
      @http_adapter.put(url, contents)
    end
  end

  defp get_upload_url(bucket, filename) do
    Minio.presign_put_object(
      client(),
      bucket_name: bucket,
      object_name: filename
    )
  end

  @impl true
  def download(bucket, filename) do
    with {:ok, url} <- get_download_url(bucket, filename) do
      @http_adapter.get(url)
    end
  end

  defp get_download_url(bucket, filename) do
    Minio.presign_get_object(
      client(),
      bucket_name: bucket,
      object_name: filename
    )
  end

  @impl true
  def delete(_bucket, _filename) do
    # The Minio client does not provide a delete function.
    {:ok, %{status_code: 204, body: ""}}
  end

  defp client() do
    %Minio{
      endpoint: config()[:minio_url],
      access_key: config()[:minio_access_key],
      secret_key: config()[:minio_secret_key]
    }
  end

  defp config(), do: Application.get_env(:jade, :storage)
end

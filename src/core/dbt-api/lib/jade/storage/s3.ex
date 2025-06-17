defmodule Jade.Storage.S3 do
  @moduledoc """
  The Storage Adapter for S3 used in production.
  """

  @behaviour Jade.Storage.Adapter
  @http_adapter Application.compile_env(:jade, :http_adapter)

  @impl true
  def upload(bucket, filename, contents) do
    with {:ok, url} <- get_presigned_url(bucket, filename, :put) do
      @http_adapter.put(url, contents)
    end
  end

  @impl true
  def download(bucket, filename) do
    with {:ok, url} <- get_presigned_url(bucket, filename, :get) do
      @http_adapter.get(url)
    end
  end

  @impl true
  def delete(bucket, filename) do
    with {:ok, url} <- get_presigned_url(bucket, filename, :delete) do
      @http_adapter.delete(url)
    end
  end

  defp get_presigned_url(bucket, filename, http_operation) do
    :s3
    |> ExAws.Config.new()
    |> ExAws.S3.presigned_url(http_operation, bucket, filename)
  end
end

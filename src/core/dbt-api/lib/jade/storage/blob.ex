defmodule Jade.Storage.Blob do
  @moduledoc """
  The Storage Adapter for Azure Blob, used in production.
  """

  @behaviour Jade.Storage.Adapter

  @impl true
  def upload(bucket, filename, contents) do
    filename = sanitize_filename(filename)
    Azurex.Blob.put_blob(filename, contents, "text/plain", bucket)
  end

  @impl true
  def download(bucket, filename) do
    filename = sanitize_filename(filename)

    with {:ok, contents} <- Azurex.Blob.get_blob(filename, bucket) do
      {:ok, %{status_code: 200, body: contents}}
    end
  end

  @impl true
  def delete(bucket, filename) do
    filename = sanitize_filename(filename)

    case Azurex.Blob.delete_blob(filename, bucket) do
      :ok -> {:ok, %{status_code: 204, body: ""}}
      {:error, :not_found} -> {:ok, %{status_code: 204, body: ""}}
      error -> error
    end
  end

  # Azurex.Blob expects a filename without leading "/"
  defp sanitize_filename("/" <> filename), do: filename
  defp sanitize_filename(filename), do: filename
end

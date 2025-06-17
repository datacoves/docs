defmodule Jade.Storage do
  @moduledoc """
  The interface for uploading and downloading files from and to Minio or S3.
  """

  require Logger

  def upload(filename, content) do
    response = adapter().upload(bucket(), filename, content)

    with {:ok, _body} <- handle_response(response) do
      :ok
    end
  end

  def download(filename) do
    response = adapter().download(bucket(), filename)
    handle_response(response)
  end

  def delete(filename) do
    response = adapter().delete(bucket(), filename)

    with {:ok, _body} <- handle_response(response) do
      :ok
    end
  end

  defp handle_response(:ok), do: :ok
  defp handle_response({_result, response}), do: handle_response(response)
  defp handle_response(%{status_code: 200, body: body}), do: {:ok, body}
  defp handle_response(%{status_code: 204, body: body}), do: {:ok, body}
  defp handle_response(%{status_code: 404}), do: {:error, :not_found}

  defp handle_response(%{status_code: error_code, body: body}) do
    Logger.error("HTTP Request failed - #{error_code} - #{inspect(body)}")
    {:error, :http_request_failed}
  end

  defp adapter(), do: Application.get_env(:jade, :storage)[:adapter]
  defp bucket(), do: Application.get_env(:jade, :storage)[:bucket]
end

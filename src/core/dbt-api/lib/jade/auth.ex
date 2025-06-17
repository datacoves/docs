defmodule Jade.Auth do
  @moduledoc """
  Verifies an ApiKey against the Datacoves API and fetches its details.
  """

  require Logger

  @http_adapter Application.compile_env(:jade, :http_adapter)

  @doc """
  Fetches permissions for a user through the Datacoves token verify API.
  """
  def fetch_api_key_details(bearer_token) do
    headers = [{"Authorization", "Token #{bearer_token}"}, {"Content-Type", "application/json"}]

    case @http_adapter.get(verify_url(), headers) do
      {:ok, %HTTPoison.Response{status_code: status_code, body: body}} when status_code < 400 ->
        {:ok, Jason.decode!(body)}

      {:ok, %HTTPoison.Response{status_code: 404}} ->
        {:error, :api_key_not_found}

      {:ok, %HTTPoison.Response{status_code: status_code, body: body}} ->
        Logger.error("Verifying ApiKey returned #{status_code} with #{inspect(body)}")
        {:error, :invalid_api_key}

      {:error, %HTTPoison.Error{reason: reason}} ->
        {:error, reason}
    end
  end

  defp verify_url(), do: Application.get_env(:jade, :datacoves_verify_url)
end

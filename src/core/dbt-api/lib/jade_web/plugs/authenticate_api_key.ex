defmodule JadeWeb.Plugs.AuthenticateApiKey do
  @moduledoc """
  Verifies a request made by a Service Account like e.g. the Airflow Service Account
  which automatically uploads the manifest.json to Jade after a DAGRun completes.

  This plug takes a bearer token, compares it with a Django AuthToken in the Datacoves
  database, and checks that the user associated with the token has the correct permission
  to upload manifests to the environment specified in the parameters.
  """

  require Logger

  alias Jade.Auth

  alias JadeWeb.API.FallbackController
  alias JadeWeb.Plugs.Utils

  def init(opts), do: opts

  def call(conn, _opts) do
    with {:ok, bearer_token} <- Utils.get_bearer_token(conn),
         {:ok, api_key_details} <- Auth.fetch_api_key_details(bearer_token),
         :ok <- check_permission(conn, api_key_details) do
      conn
    else
      {:error, :missing_api_key} ->
        message = "Missing API Key. Please create a Bearer Token first."
        FallbackController.unauthenticated(conn, message)

      {:error, :invalid_api_key} ->
        message = "Invalid API Key. Please use a valid Bearer Token."
        FallbackController.unauthenticated(conn, message)

      {:error, :api_key_not_found} ->
        message = "Invalid API Key. Please use a valid Bearer Token."
        FallbackController.unauthenticated(conn, message)

      {:error, :no_account_permission} ->
        message = "Invalid Account in Path. You have no accces to this account."
        FallbackController.unauthenticated(conn, message)

      {:error, :no_project_permission} ->
        message = "Invalid Project in Path. You have no accces to this project."
        FallbackController.unauthenticated(conn, message)

      {:error, :no_environment_permission} ->
        message = "Invalid Environment in Path. You have no accces to this environment."
        FallbackController.unauthenticated(conn, message)

      {:error, :missing_path_parameter} ->
        message = "Invalid Path. You requested a non-existent path."
        FallbackController.unauthenticated(conn, message)
    end
  end

  defp check_permission(
         %{params: %{"account_id" => account_id}} = _conn,
         %{"account_ids" => account_ids} = _api_key_details
       ) do
    with {account_id, ""} <- Integer.parse(account_id),
         true <- account_id in account_ids do
      :ok
    else
      _error ->
        {:error, :no_account_permission}
    end
  end

  defp check_permission(
         %{params: %{"project_slug" => project_slug}} = _conn,
         %{"projects" => project_slugs} = _api_key_details
       ) do
    if project_slug in project_slugs do
      :ok
    else
      {:error, :no_project_permission}
    end
  end

  defp check_permission(
         %{params: %{"environment_slug" => environment_slug}} = _conn,
         %{"environments" => environment_slugs} = _api_key_details
       ) do
    if environment_slug in environment_slugs do
      :ok
    else
      {:error, :no_environment_permission}
    end
  end

  defp check_permission(conn, api_key_details) do
    Logger.error(
      "AuthenticateApiKey missed a path parameter or api key details: #{inspect(conn.params)} - #{inspect(api_key_details)}"
    )

    {:error, :missing_path_parameter}
  end
end

defmodule Support.Mocks.HTTPoisonMock do
  alias Datacoves.AuthTokens.AuthTokenRepo

  @file_manifest File.read!("./test/support/fixtures/manifest.json")
                 |> Jason.decode!()
                 |> Jason.encode!()

  # Airflow.Repos Tests

  def get("enabled-wo-pods-airflow-postgresql.dcw-enabled-wo-pods.svc.cluster.local:5432") do
    {:error, %HTTPoison.Error{reason: :nxdomain}}
  end

  def get("enabled-airflow-postgresql.dcw-enabled.svc.cluster.local:5432") do
    {:error, %HTTPoison.Error{reason: :closed}}
  end

  def get("env-wo-airflow-airflow-postgresql.dcw-env-wo-airflow.svc.cluster.local:5432") do
    {:error, %HTTPoison.Error{reason: :not_found}}
  end

  # JobController Test

  def get("airflow1-airflow-postgresql.dcw-airflow1.svc.cluster.local:5432") do
    {:error, %HTTPoison.Error{reason: :closed}}
  end

  def get("airflow2-airflow-postgresql.dcw-airflow2.svc.cluster.local:5432") do
    {:error, %HTTPoison.Error{reason: :closed}}
  end

  # Storage Mock for ManifestRepo and Internal.{FileController, ManifestController} Tests

  def get("http://localhost:9000/jade-dev//fail-upload" <> _path) do
    {:ok, %HTTPoison.Response{status_code: 400, body: "bad request"}}
  end

  def get("http://localhost:9000/jade-dev" <> _path) do
    {:ok, %HTTPoison.Response{status_code: 200, body: @file_manifest}}
  end

  def put("http://localhost:9000/jade-dev" <> _path, "fail-upload") do
    {:ok, %HTTPoison.Response{status_code: 400, body: "bad request"}}
  end

  def put("http://localhost:9000/jade-dev" <> _path, _content) do
    {:ok, %HTTPoison.Response{status_code: 200, body: nil}}
  end

  # AuthenticateApiKey Tests

  def get(
        "https://api.datacoveslocal.com/api/datacoves/verify",
        [{"Authorization", "Token " <> token} | _] = _headers
      ) do
    handle_bearer_token(token)
  end

  defp handle_bearer_token("invalid-token") do
    {:ok, %HTTPoison.Response{status_code: 401, body: "Invalid token"}}
  end

  defp handle_bearer_token("network-error") do
    {:error, %HTTPoison.Error{reason: "closed"}}
  end

  defp handle_bearer_token(auth_token_key) do
    AuthTokenRepo.get_by(key: auth_token_key) |> build_api_key_response()
  end

  defp build_api_key_response({:error, :not_found}) do
    {:ok, %HTTPoison.Response{status_code: 404, body: "Not found"}}
  end

  defp build_api_key_response({:ok, auth_token}) do
    permissions = Enum.map(auth_token.user.permissions, & &1.name)

    extended_groups =
      auth_token.user.groups
      |> Enum.map(& &1.extended_group)
      |> List.flatten()

    accounts = Enum.map(extended_groups, & &1.account) |> Enum.reject(&is_nil/1)
    environments = Enum.map(extended_groups, & &1.environment) |> Enum.reject(&is_nil/1)
    projects = Enum.map(extended_groups, & &1.project) |> Enum.reject(&is_nil/1)

    body = %{
      "permissions" => permissions,
      "account_ids" => Enum.map(accounts, & &1.id),
      "accounts" => Enum.map(accounts, & &1.slug),
      "environment_ids" => Enum.map(environments, & &1.id),
      "environments" => Enum.map(environments, & &1.slug),
      "project_ids" => Enum.map(projects, & &1.id),
      "projects" => Enum.map(projects, & &1.slug)
    }

    encoded_body = Jason.encode!(body)

    {:ok, %HTTPoison.Response{status_code: 200, body: encoded_body}}
  end

  def delete(_url), do: {:ok, %HTTPoison.Response{status_code: 200}}
end

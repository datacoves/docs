defmodule Airflow.Repos do
  @moduledoc """
  We may have multiple Postgres databases in a cluster, one per Environment.

  This module starts dynamic Repos to connect to them, one Repo per Database,
  that means one Repo per Environment.

  The database might not be available yet when we start this application
  because the Kubernetes pods are started in parallel. If a database is
  unavailable when the Repo is started, the Repo will not be started. We
  test - very stupidly - whether a Postgres pod is available by making a
  GET http request to it.

  If an Environment is created after this process started and we try to fetch
  the Repo pid for it, the Supervisor starts a new Repo if the environment
  has Airflow enabled. Otherwise, it returns `{:error, :not_found}`.

  Any call to the Postgres databases must go through this module.
  """
  use Supervisor

  @me __MODULE__
  @http_adapter Application.compile_env(:jade, :http_adapter)

  require Logger

  alias Airflow.Repo

  alias Jade.Environments.EnvironmentRepo
  alias Jade.Environments.Environment

  def start_link(args) do
    Supervisor.start_link(@me, [args], name: Keyword.get(args, :name, @me))
  end

  def init(_args) do
    repos = build_repo_specs()
    Supervisor.init(repos, strategy: :one_for_one)
  end

  @spec get_repo_for_environment(Environment.t()) :: {:ok, pid()} | {:error, :not_found, binary()}
  def get_repo_for_environment(%Environment{} = environment, supervisor \\ @me) do
    supervisor
    |> Supervisor.which_children()
    |> Enum.find(fn {id, _pid, _type, _repo} -> id == environment.slug end)
    |> maybe_return_repo(environment, supervisor)
  end

  defp build_repo_specs() do
    EnvironmentRepo.list()
    |> Enum.map(&do_build_repo_spec/1)
    |> Enum.reject(&is_nil/1)
  end

  # Connect to an active Airflow database in Production
  def do_build_repo_spec(
        %Environment{
          services: %{
            "airflow" => %{"enabled" => true}
          },
          airflow_config: %{"db" => %{"external" => true} = db_config},
          slug: slug
        } = _environment
      ) do
    %{
      "host" => host,
      "port" => port,
      "user" => username,
      "password" => password,
      "database" => database
    } = db_config

    url = "postgresql://#{username}:#{password}@#{host}:#{port}/#{database}"
    config = build_connection(slug, url, Mix.env())
    %{id: slug, start: {Repo, :start_link, [config]}}
  end

  # Connect to an active Airflow database in development or test
  def do_build_repo_spec(
        %Environment{
          services: %{
            "airflow" => %{"enabled" => true}
          },
          slug: slug
        } = _environment
      ) do
    domain = "#{slug}-airflow-postgresql.dcw-#{slug}.svc.cluster.local:5432"

    case @http_adapter.get(domain) do
      # A :closed error means that the Postgres pod is available but refused our connecton request
      # But we can connect to it.
      {:error, %HTTPoison.Error{reason: :closed}} ->
        url = "postgresql://postgres:postgres@#{domain}/postgres"
        config = build_connection(slug, url, Mix.env())
        %{id: slug, start: {Repo, :start_link, [config]}}

      # Any other error means that the Postgres pod is not yet available and we shouldn't
      # start a Repo for it.
      _error ->
        Logger.error("Cannot connect to Airflow repo at: #{domain}")
        nil
    end
  end

  def do_build_repo_spec(%Environment{} = _environment), do: nil

  defp maybe_return_repo({_id, repo_pid, _type, _repo}, _environment, _supervisor) do
    {:ok, repo_pid}
  end

  defp maybe_return_repo(nil, environment, supervisor) do
    case do_build_repo_spec(environment) do
      nil -> {:error, :not_found, "Airflow Repo for Environment #{environment.slug} not found."}
      child_spec -> Supervisor.start_child(supervisor, child_spec)
    end
  end

  # In test tests, connect to the local postgres as defined in test.exs instead
  defp build_connection(name, _url, :test) do
    query_args = ["SET search_path TO #{name}", []]
    [name: nil, restart: :transient, pool_size: 1, after_connect: {Postgrex, :query!, query_args}]
  end

  # In dev and prod, connect to the external postgres pod
  defp build_connection(_name, url, _env) do
    sanitized_url = url |> String.split(~r/[:@]/) |> List.replace_at(2, "hidden") |> Enum.join("")
    Logger.info("Trying to connect to Airflow Repo at: #{sanitized_url}")

    [
      name: nil,
      restart: :transient,
      pool_size: 2,
      url: url
    ]
  end
end

defmodule Jade.Application do
  # See https://hexdocs.pm/elixir/Application.html
  # for more information on OTP Applications
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    connect_to_airflow = Application.get_env(:jade, :connect_to_airflow)
    start_endpoint = Application.get_env(:jade, :start_endpoint)

    children =
      [
        JadeWeb.Telemetry,
        {Phoenix.PubSub, name: Jade.PubSub},
        Jade.Repo,
        Datacoves.Repo,
        Jade.Manifests.Cleaner
      ] ++ airflow(connect_to_airflow) ++ endpoint(start_endpoint)

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: Jade.Supervisor]
    Supervisor.start_link(children, opts)
  end

  defp airflow(true), do: [Airflow.Repos]
  defp airflow(false), do: []

  defp endpoint(true), do: [JadeWeb.Endpoint]
  defp endpoint(false), do: []

  # Tell Phoenix to update the endpoint configuration
  # whenever the application is updated.
  @impl true
  def config_change(changed, _new, removed) do
    JadeWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end

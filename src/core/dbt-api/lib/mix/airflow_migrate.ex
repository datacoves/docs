defmodule Mix.Tasks.Airflow.Migrate do
  use Mix.Task

  require Logger

  alias Airflow.Repo

  @preferred_cli_env :test

  @prefixes ["airflow1", "airflow2"]

  @shortdoc "Migrates all test airflow schemas in the database"
  def run(args) do
    {opts, _, _} = OptionParser.parse(args, strict: [quiet: :boolean])
    log_level = maybe_silence_logger(opts)

    {:ok, _deps} = Application.ensure_all_started(:jade)
    {:ok, _pid} = Repo.start_link()

    priv = Repo.config() |> Keyword.get(:priv) |> Path.expand()
    priv = priv <> "/migrations"

    :ok = maybe_create_db()

    Enum.each(@prefixes, fn prefix ->
      create_prefix(prefix)
      run_migrations(prefix, priv)
    end)

    if log_level, do: Logger.configure(level: log_level)
  end

  defp maybe_silence_logger(opts) do
    if Keyword.get(opts, :quiet, false) do
      log_level = Logger.level()
      Logger.configure(level: :error)
      log_level
    end
  end

  defp maybe_create_db() do
    case Repo.__adapter__().storage_up(Repo.config()) do
      :ok -> :ok
      {:error, :already_up} -> :ok
      {:error, term} -> {:error, term}
    end
  end

  defp create_prefix(prefix) do
    query = """
    CREATE SCHEMA "#{prefix}"
    """

    Repo.query(query)
  end

  defp run_migrations(prefix, priv) do
    opts = [prefix: prefix, all: true]

    Ecto.Migrator.run(Repo, priv, :up, opts)
  end
end

defmodule Jade.Manifests.Cleaner do
  @moduledoc """
  A background job that deletes old manifest contents from the database.
  It only keeps the manifest contents of the last successful JobRun per DAG.
  """
  use GenServer

  require Logger

  alias Jade.Manifests.ManifestRepo

  # Run every minute
  @interval :timer.minutes(1)

  def start_link(init_args) do
    GenServer.start_link(__MODULE__, [init_args])
  end

  def init(_args) do
    schedule_run()
    {:ok, :initial_state}
  end

  defp schedule_run() do
    Process.send_after(self(), :clean, @interval)
  end

  def handle_info(:clean, _state) do
    schedule_run()

    count = ManifestRepo.delete_old_manifest_contents()
    Logger.debug("Deleted #{count} old manifest contents")

    {:noreply, :cleaned}
  end
end

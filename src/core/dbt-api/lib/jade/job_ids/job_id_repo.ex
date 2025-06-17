defmodule Jade.JobIds.JobIdRepo do
  use Jade, :repository

  alias Jade.JobIds.JobId

  def create(attrs) do
    %JobId{}
    |> JobId.changeset(attrs)
    |> Repo.insert()
  end

  def list() do
    Repo.all(JobId)
  end

  def get_by(attrs) do
    JobId
    |> Repo.get_by(attrs)
    |> Repo.normalize_one()
  end

  def get_or_create_by(attrs) do
    case get_by(attrs) do
      {:ok, record} -> {:ok, record}
      _error -> attrs |> Map.new() |> create()
    end
  end
end

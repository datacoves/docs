defmodule Jade.JobRunIds.JobRunIdRepo do
  use Jade, :repository

  alias Jade.JobRunIds.JobRunId

  def create(attrs) do
    %JobRunId{}
    |> JobRunId.changeset(attrs)
    |> Repo.insert()
  end

  def list() do
    Repo.all(JobRunId)
  end

  def get_by(attrs) do
    JobRunId
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

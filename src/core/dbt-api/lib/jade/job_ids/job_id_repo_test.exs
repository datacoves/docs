defmodule Jade.JobIds.JobIdRepoTest do
  use Jade.DataCase, async: true

  alias Jade.JobIds.JobIdRepo

  describe "get_by/1" do
    test "returns a record for an job_id" do
      job_id = insert(:job_id)

      {:ok, result} =
        JobIdRepo.get_by(environment_id: job_id.environment_id, dag_id: job_id.dag_id)

      assert result.id == job_id.id
    end

    test "returns an error if no job_id exists" do
      {:error, :not_found} = JobIdRepo.get_by(environment_id: 1, dag_id: "foobar")
    end
  end

  describe "get_or_create_by/1" do
    test "returns an existing job_id" do
      job_id = insert(:job_id)

      {:ok, result} =
        JobIdRepo.get_or_create_by(environment_id: job_id.environment_id, dag_id: job_id.dag_id)

      assert result.id == job_id.id

      {:ok, result} = JobIdRepo.get_or_create_by(id: job_id.id)
      assert result.id == job_id.id
    end

    test "creates a new job_id if it doesn't exist" do
      {:ok, result} = JobIdRepo.get_or_create_by(environment_id: 1, dag_id: "foobar")
      assert result.id
      assert result.dag_id == "foobar"
      assert result.environment_id == 1
    end
  end
end

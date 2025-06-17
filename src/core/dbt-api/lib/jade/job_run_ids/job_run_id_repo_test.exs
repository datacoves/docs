defmodule Jade.JobRunIds.JobRunIdRepoTest do
  use Jade.DataCase, async: true

  alias Jade.JobRunIds.JobRunIdRepo

  describe "get_by/1" do
    test "returns a record for a composite key" do
      job_run_id = insert(:job_run_id)

      {:ok, result} =
        JobRunIdRepo.get_by(
          dag_run_id: job_run_id.dag_run_id,
          environment_id: job_run_id.environment_id
        )

      assert result.id == job_run_id.id
    end

    test "returns an error if no job_run_id exists" do
      {:error, :not_found} = JobRunIdRepo.get_by(dag_run_id: 1, environment_id: 1)
    end
  end

  describe "get_or_create_by/1" do
    test "returns an existing job_run_id" do
      job_run_id = insert(:job_run_id)

      {:ok, result} =
        JobRunIdRepo.get_or_create_by(
          dag_run_id: job_run_id.dag_run_id,
          environment_id: job_run_id.environment_id
        )

      assert result.id == job_run_id.id
    end

    test "creates a new job_run_id if it doesn't exist" do
      {:ok, result} = JobRunIdRepo.get_or_create_by(dag_run_id: 1, environment_id: 2)
      assert result.id
      assert result.dag_run_id == 1
      assert result.environment_id == 2
    end
  end
end

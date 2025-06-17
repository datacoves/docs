defmodule Support.Factories.Jade do
  use ExMachina.Ecto, repo: Jade.Repo

  alias Jade.Files.File
  alias Jade.JobIds.JobId
  alias Jade.JobRunIds.JobRunId
  alias Jade.Manifests.Manifest

  def job_id_factory do
    %JobId{
      environment_id: sequence(:dag_environment_id, & &1),
      dag_id: sequence(:dag_id, &"python_sample_project_#{&1}")
    }
  end

  def job_run_id_factory do
    %JobRunId{
      environment_id: sequence(:dag_run_environment_id, & &1),
      dag_run_id: sequence(:dag_run_id, & &1)
    }
  end

  def manifest_factory do
    %Manifest{
      account_id: sequence(:manifest_account_id, & &1),
      environment_slug: "env123",
      dag_id: "yaml_dbt_dag",
      dag_run_id: 2,
      dag_run_run_id: "manual__2023-12-02T09:49:46.105347+00:00",
      job_run: build(:job_run_id)
    }
  end

  def file_factory do
    tag = "sample_tag_#{Enum.random(1..100)}"

    %File{
      filename: "#{Ecto.UUID.generate()}.json",
      tag: tag,
      contents: "testtesttest",
      environment_slug: "env123",
      path: "/environment/env123/files/#{tag}"
    }
  end
end

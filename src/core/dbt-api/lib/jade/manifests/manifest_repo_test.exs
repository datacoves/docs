defmodule Jade.Manifests.ManifestRepoTest do
  use Jade.DataCase, async: false

  alias Jade.JobRunIds.JobRunIdRepo
  alias Jade.Manifests.ManifestRepo

  @content File.read!("./test/support/fixtures/manifest.json")

  describe "create/1" do
    test "creates a new manifest" do
      attrs = insert_two_accounts_with_repos()

      # Another DagRun with the same run_id but different dag_id to test that we select the correct DagRun.
      insert(:dag_run, repo: attrs.repo_1, run_id: "manual__2023-12-02T09:49:46.105347+00:00")

      dag_run =
        insert(:dag_run, repo: attrs.repo_1, run_id: "manual__2023-12-02T09:49:46.105347+00:00")

      {:ok, res_manifest} =
        ManifestRepo.create(attrs.environment_1.slug, dag_run.dag_id, dag_run.run_id, @content)

      {:ok, res_manifest} = ManifestRepo.get(res_manifest.id)
      assert res_manifest.account_id == attrs.account_1.id
      assert res_manifest.environment_slug == attrs.environment_1.slug
      assert res_manifest.dag_id == dag_run.dag_id
      assert res_manifest.dag_run_id == dag_run.id
      assert res_manifest.dag_run_run_id == dag_run.run_id

      assert %{"metadata" => %{"dbt_version" => "1.6.9"}} =
               ManifestRepo.get_full_content(res_manifest)

      {:ok, job_run_id} = JobRunIdRepo.get_by(id: res_manifest.job_run_id)
      assert job_run_id.environment_id == attrs.environment_1.id
      assert job_run_id.dag_run_id == dag_run.id
    end
  end

  describe "get_by/1" do
    test "returns a manifest for a given job_run_id" do
      manifest = insert(:manifest)
      {:ok, res_manifest} = ManifestRepo.get_by(job_run_id: manifest.job_run_id)
      assert res_manifest.id == manifest.id
    end

    test "returns an error if no manifest exists for the given job_run_id" do
      {:error, :not_found} = ManifestRepo.get_by(job_run_id: 1)
    end
  end

  describe "get/1" do
    test "returns a manifest for a given id" do
      manifest = insert(:manifest)
      {:ok, res_manifest} = ManifestRepo.get(manifest.id)
      assert res_manifest.id == manifest.id
    end

    test "returns an error if no manifest exists for the given id" do
      {:error, :not_found} = ManifestRepo.get(1)
    end
  end

  describe "get_minimal_content/1" do
    test "returns the trimmed content of a manifest" do
      content = Jason.decode!(@content)
      manifest = insert(:manifest, content: content)

      result = ManifestRepo.get_minimal_content(manifest)

      assert %{
               # "exposures" => %{
               #   "exposure.balboa.customer_loans" => %{
               #     "fqn" => ["balboa", "L4_exposures", "customer_loans"]
               #     # removed other fields for brevity
               #   },
               #   "exposure.balboa.loans_analysis" => %{
               #     "fqn" => ["balboa", "L4_exposures", "loans_analysis"]
               #   }
               # },
               # "group_map" => %{},
               # "groups" => %{},
               "metadata" => %{
                 "generated_at" => "2024-01-18T14:38:12.611300Z",
                 "project_name" => "balboa"
                 # removed other fields for brevity
               },
               "nodes" => %{
                 "model.balboa.base_cases" => %{
                   "database" => "BALBOA_DEV",
                   "fqn" => ["balboa", "L2_bays", "covid_observations", "base_cases"],
                   "schema" => "gomezn"
                 },
                 "model.balboa.country_populations" => %{
                   "database" => "BALBOA_DEV",
                   "fqn" => ["balboa", "L1_inlets", "country_data", "country_populations"],
                   "schema" => "gomezn"
                 }
               }
             } = result
    end

    test "returns an empty map if a manifest has no content" do
      manifest = insert(:manifest, content: nil)

      result = ManifestRepo.get_minimal_content(manifest)

      assert %{
               # "exposures" => nil,
               # "group_map" => nil,
               # "groups" => nil,
               "metadata" => nil,
               "nodes" => nil
             } = result
    end
  end

  describe "delete_old_manifest_contents" do
    test "deletes old manifest contents" do
      content = Jason.decode!(@content)

      manifest_1 =
        insert(:manifest,
          dag_id: "yaml_example_dag",
          content: content,
          inserted_at: ~U[2024-01-01 10:00:00Z]
        )

      manifest_2 =
        insert(:manifest,
          dag_id: "yaml_example_dag",
          content: content,
          inserted_at: ~U[2024-01-01 11:00:00Z]
        )

      manifest_3 =
        insert(:manifest,
          dag_id: "yaml_example_dag",
          content: content,
          inserted_at: ~U[2024-01-01 12:00:00Z]
        )

      manifest_4 =
        insert(:manifest,
          dag_id: "another_dag",
          content: content,
          inserted_at: ~U[2024-01-01 13:00:00Z]
        )

      manifest_5 =
        insert(:manifest,
          dag_id: "another_dag",
          content: content,
          inserted_at: ~U[2024-01-01 14:00:00Z]
        )

      manifest_6 =
        insert(:manifest,
          dag_id: "dag_with_only_one_manifest",
          content: content,
          inserted_at: ~U[2024-01-01 15:00:00Z]
        )

      ManifestRepo.delete_old_manifest_contents()

      # The first two manifest contents should have been deleted
      assert ManifestRepo.get_full_content(manifest_1) == nil
      assert ManifestRepo.get_full_content(manifest_2) == nil
      assert ManifestRepo.get_full_content(manifest_3) == content

      # The first manifest content should have been deleted
      assert ManifestRepo.get_full_content(manifest_4) == nil
      assert ManifestRepo.get_full_content(manifest_5) == content

      # The manifest content should not have been deleted
      assert ManifestRepo.get_full_content(manifest_6) == content
    end
  end
end

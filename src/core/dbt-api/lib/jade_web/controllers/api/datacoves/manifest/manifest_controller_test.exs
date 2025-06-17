defmodule JadeWeb.API.Datacoves.ManifestControllerTest do
  use JadeWeb.ConnCase, async: false

  alias Jade.JobRunIds.JobRunId
  alias Jade.Manifests.ManifestRepo

  @fixture_path "test/support/fixtures/manifest.json"

  defp path() do
    ~p"/api/v2/datacoves/manifests"
  end

  setup %{conn: conn} do
    attrs = insert_two_accounts_with_repos()

    user = insert(:user, is_service_account: true)

    auth_token =
      insert_auth_token_for_user(user, attrs.account_1, attrs.environment_1, attrs.project_1)

    conn = put_bearer_token(conn, auth_token.key)

    dag_run =
      insert(:dag_run, repo: attrs.repo_1, run_id: "manual__2023-12-02T09:49:46.105347+00:00")

    Map.merge(attrs, %{conn: conn, user: user, dag_run: dag_run})
  end

  describe "create/2" do
    test "creates a manifest", ctx do
      params = %{
        dag_id: ctx.dag_run.dag_id,
        run_id: "manual__2023-12-02T09:49:46.105347+00:00",
        environment_slug: ctx.environment_1.slug,
        tag: "tag-123",
        file: %Plug.Upload{path: @fixture_path}
      }

      ctx.conn
      |> post(path(), params)
      |> json_response(201)

      [job_run_id] = Jade.Repo.all(JobRunId)
      {:ok, manifest} = ManifestRepo.get_by(account_id: ctx.account_1.id)

      assert manifest.account_id == ctx.account_1.id
      assert manifest.project_id == ctx.environment_1.project_id
      assert manifest.job_run_id == job_run_id.id
      assert manifest.dag_run_run_id == params.run_id
      assert manifest.tag == "tag-123"

      assert %{"metadata" => %{"dbt_version" => "1.6.9"}} =
               ManifestRepo.get_full_content(manifest)
    end

    test "creates a manifest with without job run", ctx do
      params = %{
        environment_slug: ctx.environment_1.slug,
        tag: "tag-234",
        file: %Plug.Upload{path: @fixture_path}
      }

      ctx.conn
      |> post(path(), params)
      |> json_response(201)

      {:ok, manifest} = ManifestRepo.get_by(account_id: ctx.account_1.id)

      assert manifest.account_id == ctx.account_1.id
      assert manifest.project_id == ctx.environment_1.project_id
      assert manifest.job_run_id == nil
      assert manifest.dag_run_run_id == nil
      assert manifest.tag == "tag-234"

      assert %{"metadata" => %{"dbt_version" => "1.6.9"}} =
               ManifestRepo.get_full_content(manifest)

      assert %{
               "metadata" => %{
                 "project_id" => "84e0991a380d2a451e9a7787e56e2b53"
               }
             } =
               ctx.conn
               |> get(path(), %{environment_slug: ctx.environment_1.slug, trimmed: true})
               |> json_response(200)
    end

    test "returns an error if a manifest with the same environment and tag already exists", ctx do
      insert(:manifest, environment_slug: ctx.environment_1.slug, tag: "tag-234")

      params = %{
        environment_slug: ctx.environment_1.slug,
        tag: "tag-234",
        file: %Plug.Upload{path: @fixture_path}
      }

      assert %{"errors" => %{"tag" => ["has already been taken"]}} =
               ctx.conn
               |> post(path(), params)
               |> json_response(422)
    end

    test "returns an error if a user tries to upload a manifest to another environment", ctx do
      params = %{
        dag_id: ctx.dag_run.dag_id,
        run_id: "manual__2023-12-02T09:49:46.105347+00:00",
        environment_slug: ctx.environment_2.slug,
        file: %Plug.Upload{path: @fixture_path}
      }

      assert %{
               "errors" => %{
                 "message" => "Invalid Environment in Path. You have no accces to this environment."
               }
             } =
               ctx.conn
               |> post(path(), params)
               |> json_response(401)
    end

    test "returns an error if the airflow repo of the environment is not available", ctx do
      environment =
        insert(:environment,
          project: ctx.project_1,
          services: %{"airflow" => %{"enabled" => true}},
          slug: "env-wo-airflow"
        )

      auth_token =
        insert_auth_token_for_user(ctx.user, ctx.account_1, environment, ctx.project_1)

      params = %{
        dag_id: ctx.dag_run.dag_id,
        run_id: "manual__2023-12-02T09:49:46.105347+00:00",
        environment_slug: environment.slug,
        file: %Plug.Upload{path: @fixture_path}
      }

      assert capture_log(fn ->
               assert %{
                        "errors" => %{
                          "message" => "Airflow Repo for Environment env-wo-airflow not found."
                        }
                      } =
                        ctx.conn
                        |> put_bearer_token(auth_token.key)
                        |> post(path(), params)
                        |> json_response(404)
             end) =~ "Cannot connect to Airflow repo at:"
    end
  end

  describe "show/2" do
    test "returns a minimal manifest", ctx do
      content = @fixture_path |> File.read!() |> Jason.decode!()
      manifest = insert(:manifest, content: content)

      params = %{
        dag_id: manifest.dag_id,
        environment_slug: ctx.environment_1.slug
      }

      body =
        ctx.conn
        |> get(path(), params)
        |> json_response(200)

      # %{
      #   id: manifest_id,
      #   account_id: manifest_account_id,
      #   environment_slug: manifest_environment_slug,
      #   dag_id: manifest_dag_id,
      #   dag_run_run_id: manifest_dag_run_run_id
      # } = manifest

      assert %{
               # "id" => ^manifest_id,
               # "account_id" => ^manifest_account_id,
               # "environment_slug" => ^manifest_environment_slug,
               # "dag_id" => ^manifest_dag_id,
               # "dag_run_id" => ^manifest_dag_run_run_id,
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
             } = body
    end

    test "returns an empty map if the manifest has no content", ctx do
      manifest = insert(:manifest, content: nil)

      params = %{
        dag_id: manifest.dag_id,
        environment_slug: ctx.environment_1.slug
      }

      body =
        ctx.conn
        |> get(path(), params)
        |> json_response(200)

      assert %{
               # "exposures" => nil,
               # "group_map" => nil,
               # "groups" => nil,
               "metadata" => nil,
               "nodes" => nil
             } = body
    end

    test "returns a manifest by environment and tag", ctx do
      insert(:manifest,
        environment_slug: ctx.environment_1.slug,
        tag: "tag-123",
        content: %{"name" => "test-123"}
      )

      params = %{
        tag: "tag-123",
        environment_slug: ctx.environment_1.slug,
        trimmed: false
      }

      assert %{"name" => "test-123"} =
               ctx.conn
               |> get(path(), params)
               |> json_response(200)
    end

    test "returns the latest manifest for an environment", ctx do
      _later_manifest =
        insert(:manifest,
          environment_slug: ctx.environment_1.slug,
          content: %{"manifest" => "later"},
          inserted_at: ~U[2023-01-01 12:00:00Z]
        )

      _earlier_manifest =
        insert(:manifest,
          environment_slug: ctx.environment_1.slug,
          content: %{"manifest" => "earlier"},
          inserted_at: ~U[2023-01-01 01:00:00Z]
        )

      params = %{
        environment_slug: ctx.environment_1.slug,
        trimmed: false
      }

      assert %{"manifest" => "later"} =
               ctx.conn
               |> get(path(), params)
               |> json_response(200)
    end

    test "returns a 404 if no manifest exists for a given environment_slug", ctx do
      params = %{
        environment_slug: ctx.environment_1.slug
      }

      %{"errors" => %{"message" => "Not Found"}} =
        ctx.conn
        |> get(path(), params)
        |> json_response(404)
    end

    test "returns a 404 if no manifest exists for a given dag_id", ctx do
      params = %{
        dag_id: "yaml_example_dag",
        environment_slug: ctx.environment_1.slug
      }

      %{"errors" => %{"message" => "Not Found"}} =
        ctx.conn
        |> get(path(), params)
        |> json_response(404)
    end
  end
end
